#!/usr/bin/env python
"""
Mimic daemon. Monitors files for changes and syncs them to the
appropriate destination.
"""

import fnmatch
import os
import subprocess
import sys
import time

import pyinotify
import Pyro.core

#import pynotify


##########
# Daemon #
##########

class EventHandler(pyinotify.ProcessEvent):
    """Handles pyinotify events. One method per event type."""
    needs_rsync = True  # Whether syncing is necessary
    exclude = None

    def process_event(self, filename):
        for pattern in self.exclude:
            if fnmatch.fnmatch(os.path.basename(filename), pattern):
                return
        self.needs_rsync = True

    def process_IN_CREATE(self, event):
        self.process_event(event.pathname)

    def process_IN_DELETE(self, event):
        self.process_event(event.pathname)

    def process_IN_MODIFY(self, event):
        self.process_event(event.pathname)


class GroupingThreadedNotifier(pyinotify.ThreadedNotifier):
    """A modified ThreadedNotifier that waits until no events have been seen
    for a given time amount before processing them."""

    def __init__(self, wm, eh, dest, rsync_command,
        group_within=0.1, use_pynotify=True):
        """
        Args:
            wh: WatchManager instance
            eh: EventHandler instance
            dest: Destination to sync to
            rsync_command: Command to execute when syncing
            group_within: Group events within this time period of eachother
            use_pynotify: Notify of syncs using pynotify
        """

        pyinotify.ThreadedNotifier.__init__(self, wm, eh)

        self.destination = dest
        self._mimic = mimic
        self.rsync_command = rsync_command
        self.group_within = group_within
        self.pynotify = use_pynotify

    def loop(self):
        """Main loop, which reads and processes events"""
        last_read = 0
        while not self._stop_event.isSet():
            if self.check_events(10):
                last_read = time.time()
                self.read_events()
            elif time.time() - last_read > self.group_within:
                self.process_events()
                self.act_on_events()

    def act_on_events(self):
        """Syncs source and dest using rsync if necessary"""
        # TODO Point rsync to specific files
        if self._default_proc_fun.needs_rsync:
            subprocess.call(self.rsync_command)  ## TODO: Don't printo stdout
            self._default_proc_fun.needs_rsync = False

            if self.pynotify:
                pass # TODO: fix
                #pynotify.init("mimic")
                #pynotify.Notification("Finished sync").show()


class mimic(Pyro.core.ObjBase):

    _connections = {}  # Dict of open connections
    _notifiers = {}
    _ctl_path = "/tmp/mimic_%s"  # For SSH connection sharing

    def __init__(self, daemon=None):
        """Args:
            daemon: The Pyro daemon object, so that we can shutdown.
        """
        Pyro.core.ObjBase.__init__(self)
        self.daemon = daemon

    def test_connection(self):
        """Test connection to daemon"""
        return

    def start_connection(self, dest):
        """Start a shared SSH connection."""
        try:
            address = "%s_22_%s" % (dest.split('@')[1].split(':')[0], dest.split('@')[0])
            if address not in self._connections:
                p = subprocess.Popen(['ssh', '-N', '-S', self._ctl_path % address, dest.split(':')[0]])
                self._connections[address] = p
        except IndexError:
            pass
            ## raise MimicError("Unable to connect to %s" % dest)

    def add_watch(self, path, dest, rec=True, auto_add=True, 
        exclude=None, maintain_conn=True, delete=False):
        """Start syncing a new directory.

        Args:
            path (str): The path to the directory to sync.
            dest (str): The destination to sync to formatted rsync-style.
            rec (Bool): Recursively watch and sync the path.
            auto_add (Bool): Automatically start watching newly created dirs.
            exclude (list of str): A list of file extensions to ignore
            maintain_conn (Bool): Maintain a constant connection to remote
                to reduce transfer times.
            delete (Bool): Delete extraneous files from remote dirs.
        """

        if exclude is None:
            exclude = []
        
        ## Validate input
        if not os.path.exists(path):
            raise MimicError("Source path does not exist.")
        if path in self._notifiers:
            raise MimicError("Directory already being watched.")

        wm = pyinotify.WatchManager()
        eh = EventHandler()
        eh.exclude = exclude
        mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY

        if maintain_conn:
            self.start_connection(dest)

        # Construct rsync command
        cmd = ['/usr/bin/rsync']  #TODO let user specify path to rsync
        if delete:
            cmd.append('--delete')
        for pattern in exclude:
            cmd.append('--exclude=%s' % pattern)
        cmd.append('-avhzS' if rec else '-vhzS')
        cmd.extend(['-q', path, dest])

        self._notifiers[path] = GroupingThreadedNotifier(wm, eh, dest=dest, 
            rsync_command=cmd)
        self._notifiers[path].start()

        wdd = wm.add_watch(path, mask, rec=rec, auto_add=auto_add)
    
    def list_watches(self):
        """Returns a string listing all currently active watches"""
        # TODO return list, let client handle appearance
        ret = "### Currently active watches ###\n"
        for watch, notifier in self._notifiers.iteritems():
            ret += "%s syncing to%s\n" % (repr(watch), repr(notifier.destination))
        return ret

    def rm_watch(self, watch):
        """Stop the notifier with the given path"""
        if watch not in self._notifiers:
            raise MimicError("No such watch directory: %s" % watch)
        self._notifiers[watch].stop()
        del self._notifiers[watch]
    
    def shutdown(self):
        """Shut down the daemon"""
        os.remove('/tmp/mimic_daemon')
        for address, p in self._connections.iteritems():
            if not p.returncode:
                p.terminate()
        self.daemon.shutdown()


##############
# Exceptions #
##############

class MimicError(Exception):
    pass


###########################
# Start and access daemon #
###########################

def start(fork=True):
    """Start the Mimic daemon."""
    Pyro.core.initServer()
    daemon = Pyro.core.Daemon(host='127.0.0.1')
    uri = daemon.connect(mimic(daemon=daemon), "mimic")
    with open('/tmp/mimic_daemon', 'w') as f:
        f.write(str(uri))
    if fork:
        pid = os.fork()
        if pid:
            return uri

    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        daemon.shutdown()
    os._exit(os.EX_OK)


def get():
    """Try to return a running Mimic daemon"""
    try:
        with open("/tmp/mimic_daemon") as f:
            uri = f.read()
    except IOError:
        raise MimicError("Mimic not running, please start.")

    daemon = Pyro.core.getProxyForURI(uri)

    try:
        daemon.test_connection()
    except Pyro.errors.ProtocolError:
        raise MimicError("Mimic not running, please start.")

    return daemon
