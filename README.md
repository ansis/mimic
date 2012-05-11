# Mimic

A tool for making remote directories mimic local directories. Mimic monitors local files for changes, instantly syncing them to their destination.

Mimic has the ability to:

- exclude certain paths
- maintain an open SSH connection for faster transfers



### Dependencies

- [Pyinotify](https://github.com/seb-m/pyinotify)
- [Pyro](http://irmen.home.xs4all.nl/pyro/)
- Rsync


### Basic Usage

Start the Mimic daemon:

    $ mimic start

Start syncing a local path to a remote destination (in rsync format):

    $ mimic add path/to/dir user@example.com:path/to/dest --exclude *.ext

Stop syncing a path:

    $ mimic rm path/to/dir

Stop the daemon:

    $ mimic stop

For more information, and options:

    $ mimic -h

### TODO

- Optional configuration file
- Handle rsync dependency
- Tests
