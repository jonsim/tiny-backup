# Table of Contents

- [tiny-backup](#tiny-backup)
  - [Dependencies](#dependencies)
  - [License](#license)
- [Documentation](#documentation)
- [Remaining work](#remaining-work)

# tiny-backup

A micro backup manager, designed to be simple, unobtrusive and configurable.
Designed for maintaining and enforcing lightweight backup strategies.

**NB: tiny-backup is currently under development. See the
[Remaining work](#remaining-work) section for current status.**

hello

tiny-backup is little more than a glorified wrapper around rsync and tar/pgp
as described in the configuration file.

&copy; Copyright 2017 Jonathan Simmonds


## Dependencies

- rsync (tested with 3.1.1)
- GNU tar (tested with 1.28) (only needed if bundling is required)
- GPG (tested with 1.4.20) and configured keys (only needed if encryption is
  required)
All of the above are expected to be on the `$PATH`.


## License

All files are licensed under
[the MIT license](https://github.com/jonsim/tiny-backup/blob/master/LICENSE).

Only the file `backup` makes up the functional part of the project and may be
distributed alone providing the copyright &amp; license header in it remains
intact.


# Documentation

TODO


# Remaining work

TODO
