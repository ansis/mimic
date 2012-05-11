#!/usr/bin/env python
"""
Client script for Mimic.
"""

import argparse
import os
import sys

import mimic.daemon
import Pyro.core
import Pyro.errors


def start_daemon(args):
    fork = not args.no_fork
    mimic.daemon.start(fork=fork)
    print "Daemon started."


def stop_daemon(args):
    daemon.shutdown()
    print "Daemon shut down."


def add(args):
    """Add a new watch directory"""
    source = os.path.abspath(args.source)
    destination = os.path.abspath(args.destination)

    daemon.add_watch(
        source,
        destination, 
        delete=args.delete, 
        rec=not args.no_recurse,
        auto_add=not args.no_autoadd,
        maintain_conn=not args.no_maintain,
        exclude=args.exclude)
    print "Successfully added."


def rm(args):
    """Stop a particular transfer"""
    daemon.del_watch(args.source)
    print "Watch directory removed"


def list_watches(args):
    """List watches"""
    print daemon.list_watches()


def main():
    """Entry point"""
    global daemon

    parser = argparse.ArgumentParser(description='Mimic some files.')
    subparsers = parser.add_subparsers(dest='subparser_name')

    parser_add = subparsers.add_parser('add', help='Add a new watch')
    parser_add.add_argument('source', help='Source to be watched.')
    parser_add.add_argument('destination', help='Destination, in rsync format.')
    parser_add.add_argument('--delete', action='store_true', default=False, help="Delete extraneous files from destination dir.")
    parser_add.add_argument('--no-maintain', action='store_true', default=False, help="Don't maintain an open SSH connection. Slower!")
    parser_add.add_argument('--no-autoadd', action='store_true', default=False, help="Don't automatically add newly created stuff")
    parser_add.add_argument('--no-recurse', action='store_true', default=False, help="Don't recurse.")
    parser_add.add_argument('--exclude', nargs='+', help="Exclude files with the following extensions")
    parser_add.set_defaults(func=add)

    parser_rm = subparsers.add_parser('rm', help='rm a watch dir based on path')
    parser_rm.add_argument('source', help='Path to watchdirs source')
    parser_rm.set_defaults(func=rm)

    parser_list = subparsers.add_parser('list', help="List current watches")
    parser_list.set_defaults(func=list_watches)

    parser_start = subparsers.add_parser('start', help="Start the daemon")
    parser_start.add_argument('--no-fork', help="Don't fork")
    parser_start.set_defaults(func=start_daemon)

    parser_stop = subparsers.add_parser('stop', help="Stop the daemon")
    parser_stop.set_defaults(func=stop_daemon)

    args = parser.parse_args()

    try:
        if args.subparser_name != "start":
            daemon = mimic.daemon.get()

        args.func(args)
    except mimic.daemon.MimicError as e:
        print e
