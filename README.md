# Table of Contents

- [tiny-backup](#tiny-backup)
  - [Dependencies](#dependencies)
  - [License](#license)
- [Documentation](#documentation)
- [Remaining work](#remaining-work)

# tiny-backup

[![Build Status](https://travis-ci.org/jonsim/tiny-backup.svg?branch=master)](https://travis-ci.org/jonsim/tiny-backup)

A micro backup manager, designed to be simple, unobtrusive and configurable.
Designed for maintaining and enforcing lightweight backup strategies.

**NB: tiny-backup is currently under development. See the
[Remaining work](#remaining-work) section for current status.**

tiny-backup is little more than a glorified wrapper around rsync and tar/pgp
as described in the configuration file.

&copy; Copyright 2017 Jonathan Simmonds


## Dependencies

- Python &ge; 2.6 (&ge; 2.7 for running the tests)
- rsync &ge; 3.0.0
- tar (tested with 1.28) (only needed if archiving is required)
- xz (tested with 5.1.0) (only needed if compression is required)
- GPG (tested with 1.4.20) (only needed if encryption is required) (it is
  assumed keys are correctly configured)

All of the above are expected to be on the `$PATH`. NB: No explicit effort is
made to ensure the output, particularly of GPG, is of a particular format. It is
assumed the machine on which any necessary unencryption will be performed has
a compatible GPG implementation. This is an area for possible future
improvement.


## License

All files are licensed under
[the MIT license](https://github.com/jonsim/tiny-backup/blob/master/LICENSE).

Only the file `backup.py` makes up the functional part of the project and may be
distributed alone providing the copyright &amp; license header in it remains
intact.


# Documentation

It is probably most useful to run `backup.py` on the system from which the
backups originate, typically as a cron job (i.e. a 'push' setup). In this case
the config file would contain references in `src` fields to local paths and in
`dest` fields either to a remote host or local directory (which may or may not
be a remote mount).

It is also possible, to run `backup.py` on the remote host on which the backups
will end up (i.e. a 'pull' setup). This is most useful when the machine from
which the backups originate is not Unix-based or lacks a cron implementation. In
this case the config file would contain references in `src` fields to a remote
host or mount and in `dest` fields to a local directory.

The `src` and `dest` fields are passed verbatim to the rsync client. As a result
it is possible to communicate with an rsync daemon if necessary (i.e. no remote
shell) as well as using other more advanced features.


# Remaining work

TODO
