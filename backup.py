#!/usr/bin/env python
# (c) Copyright 2017 Jonathan Simmonds
#
# Licensed under the MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""
A micro backup manager, designed to be lightly configurable, simple and
unobtrusive. Useful for maintaining lightweight backups.

Maintained at https://github.com/jonsim/tiny-backup
"""
import argparse     # ArgumentParser
import ConfigParser # SafeConfigParser
import os           # makedirs
import os.path      # exists, isfile, isdir, expanduser
import subprocess   # check_output
import shutil       # rmtree
import sys          # stdout
import tempfile     # mkdtemp

__version__ = '1.0.0'

DEST_KEY = 'dest'
SRC_KEY = 'src'
ARCHIVE_KEY = 'archive'
COMPRESS_KEY = 'compress'
ENCRYPT_KEY = 'encrypt'
DEFAULTS = {
    ARCHIVE_KEY: 'no',
    COMPRESS_KEY: 'no',
    ENCRYPT_KEY: 'no',
}

_TEMPDIR = None

def make_tempdir():
    """
    Retrieves a temporary directory, creating it if necessary.

    Returns:
        string path to a temporary directory.
    """
    global _TEMPDIR
    if not _TEMPDIR:
        _TEMPDIR = tempfile.mkdtemp()
    return _TEMPDIR

def archive_path(dest, src, excludes=None, verbose=False):
    """
    Packs a file or directory into a .tar archive.

    Args:
        dest:       string path for the destination file for the archive. Must
            end with '.tar'.
        src:        string path for the source file or directory for the
            archive.
        excludes:   list of strings of paths to exclude from the archive. May be
            None or an empty list to include all files from source. Defaults to
            None.
        verbose:    boolean, True to output verbose status to stdout. Defaults
            to False.

    Raises:
        OSError:    if the 'tar' command fails for any reason.
    """
    assert dest and dest.endswith('.tar') and not os.path.isdir(dest) and \
           os.path.isdir(os.path.dirname(dest))
    assert src and os.path.exists(src)
    cmd = ['tar']
    cmd.append('--create')
    if verbose:
        print '\narchive_path(%s, %s)' % (dest, src)
        cmd.append('--verbose')
    if excludes:
        for exclude in excludes:
            cmd.append('--exclude=%s' % (exclude))
    cmd.append('--file')
    cmd.append(dest)
    cmd.append('--directory')
    cmd.append(os.path.dirname(src))
    cmd.append(os.path.basename(src))
    sys.stdout.write(subprocess.check_output(cmd))

def unarchive_path(dest, src, verbose=False):
    """
    Extracts a .tar archive into a directory.

    Args:
        dest:       string path for the destination *directory* into which the
            archive contents will be extracted. NB: This is the directory to
            extract into, not the final path for the contents of the archive.
        src:        string path for the source archive file. Must end with
            '.tar'.
        verbose:    boolean, True to output verbose status to stdout. Defaults
            to False.

    Raises:
        OSError:    if the 'tar' command fails for any reason.
    """
    assert dest and os.path.isdir(dest)
    assert src and src.endswith('.tar') and os.path.isfile(src)
    cmd = ['tar']
    cmd.append('--extract')
    if verbose:
        print '\nunarchive_path(%s, %s)' % (dest, src)
        cmd.append('--verbose')
    cmd.append('--file')
    cmd.append(src)
    cmd.append('--directory')
    cmd.append(dest)
    sys.stdout.write(subprocess.check_output(cmd))

def compress_path(dest, src, verbose=False):
    """
    Compresses a file into an xz-compressed file.

    Args:
        dest:       string path for the destination file. Must end with '.xz'.
        src:        string path for the source file to compress.
        verbose:    boolean, True to output verbose status to stdout. Defaults
            to False.

    Raises:
        OSError:    if the 'xz' command fails for any reason.
    """
    assert dest and dest.endswith('.xz') and not os.path.isdir(dest) and \
           os.path.isdir(os.path.dirname(dest))
    assert src and os.path.isfile(src)
    cmd = ['xz']
    if verbose:
        print '\ncompress_path(%s, %s)' % (dest, src)
        cmd.append('--verbose')
    else:
        cmd.append('--quiet')
    cmd.append('--keep')
    cmd.append('--stdout')
    cmd.append('--compress')
    cmd.append(src)
    try:
        dest_file = open(dest, 'w')
        subprocess.check_call(cmd, stdout=dest_file)
    finally:
        dest_file.close()

def uncompress_path(dest, src, verbose=False):
    """
    Uncompresses an xz-compressed file into it's original format.

    Args:
        dest:       string path for the destination uncompressed file.
        src:        string path for the source compressed file. Must end with
            '.xz'.
        verbose:    boolean, True to output verbose status to stdout. Defaults
            to False.

    Raises:
        OSError:    if the 'xz' command fails for any reason.
    """
    assert dest and not os.path.isdir(dest) and \
           os.path.isdir(os.path.dirname(dest))
    assert src and src.endswith('.xz') and os.path.isfile(src)
    cmd = ['xz']
    if verbose:
        print '\nuncompress_path(%s, %s)' % (dest, src)
        cmd.append('--verbose')
    else:
        cmd.append('--quiet')
    cmd.append('--keep')
    cmd.append('--stdout')
    cmd.append('--decompress')
    cmd.append(src)
    try:
        dest_file = open(dest, 'w')
        subprocess.check_call(cmd, stdout=dest_file)
    finally:
        dest_file.close()

def encrypt_path(dest, src, homedir=None, verbose=False):
    """
    Encrypts a file into a gpg-encrypted file.

    Args:
        dest:       string path for the destination file. Must end with '.gpg'.
        src:        string path for the source file to encrypt.
        homedir:    string path for the location of the GPG home directory to
            use. May be None to use the default location for the machine's GPG
            implementation (typically ~/gnupg). Defaults to None.
        verbose:    boolean, True to output verbose status to stdout. Defaults
            to False.

    Raises:
        OSError:    if the 'gpg' command fails for any reason.
    """
    assert dest and dest.endswith('.gpg') and not os.path.isdir(dest) and \
           os.path.isdir(os.path.dirname(dest))
    assert src and os.path.isfile(src)
    cmd = ['gpg']
    if verbose:
        print '\nencrypt_path(%s, %s)' % (dest, src)
        cmd.append('--verbose')
    else:
        cmd.append('--quiet')
    if homedir:
        cmd.append('--homedir')
        cmd.append(homedir)
    cmd.append('--default-recipient-self')
    cmd.append('--output')
    cmd.append(dest)
    cmd.append('--encrypt')
    cmd.append(src)
    sys.stdout.write(subprocess.check_output(cmd))

def unencrypt_path(dest, src, homedir=None, verbose=False):
    """
    Decrypts a gpg-encrypted file into its original format.

    Args:
        dest:       string path for the destination decrypted file.
        src:        string path for the source file to decrypt. Must end with
            '.gpg'.
        homedir:    string path for the location of the GPG home directory to
            use. May be None to use the default location for the machine's GPG
            implementation (typically ~/gnupg). Defaults to None.
        verbose:    boolean, True to output verbose status to stdout. Defaults
            to False.

    Raises:
        OSError:    if the 'gpg' command fails for any reason.
    """
    assert dest and not os.path.isdir(dest)and \
           os.path.isdir(os.path.dirname(dest))
    assert src and src.endswith('.gpg') and os.path.isfile(src)
    cmd = ['gpg']
    if verbose:
        print '\nunencrypt_path(%s, %s)' % (dest, src)
        cmd.append('--verbose')
    else:
        cmd.append('--quiet')
    if homedir:
        cmd.append('--homedir')
        cmd.append(homedir)
    cmd.append('--default-recipient-self')
    cmd.append('--output')
    cmd.append(dest)
    cmd.append('--decrypt')
    cmd.append(src)
    sys.stdout.write(subprocess.check_output(cmd))

def copy_path(dest, src, excludes=None, verbose=False):
    """
    Copies a path to another location.

    Args:
        dest:       string path for the destination copied file or directory.
        src:        string path for the source file or directory to copy.
        excludes:   list of strings of paths to exclude from the copy. May be
            None or an empty list to include all files from source. Defaults to
            None.
        verbose:    boolean, True to output verbose status to stdout. Defaults
            to False.

    Raises:
        OSError:    if the 'rsync' command fails for any reason.
    """
    assert dest and os.path.isdir(os.path.dirname(dest))
    assert src and os.path.exists(src)
    cmd = ['rsync']
    if verbose:
        print '\ncopy_path(%s, %s)' % (dest, src)
        cmd.append('--verbose')
    else:
        cmd.append('--quiet')
    cmd.append('--archive')         # Preserve metadata (-a)
    cmd.append('--delete')          # Delete extra files
    cmd.append('--compress')        # Compress xfer data (-z)
    cmd.append('--protect-args')    # Preserve whitespace (-s)
    if excludes:
        for exclude in excludes:
            cmd.append('--filter=exclude_%s' % (exclude))
    cmd.append(src)
    cmd.append(dest)
    sys.stdout.write(subprocess.check_output(cmd))

def resolve_relative_path(path, config_path):
    """
    Resolves relative paths into absolute paths relative to the config file.

    Args:
        path:           string (potentially) relative path to resolve.
        config_path:    string path to the config file to resolve relative to.

    Returns:
        string absolute path (unaltered if 'path' was already absolute).
    """
    if os.path.isabs(path):
        return path
    return os.path.join(os.path.dirname(config_path), path)

def get_out_filename(dirname, src, extension):
    """
    Forms a filename from a dir-name, file-name and file-extension.

    Args:
        dirname:    string path to directory to use.
        src:        string path to file whose basename to use.
        extension:  string file extension (without preceding '.') to use.

    Returns:
        string path formed from the given components.
    """
    return os.path.join(dirname, '%s.%s' % (os.path.basename(src), extension))

def process_section(config, section, config_path, verbose=False, gpg_home=None):
    """
    Process a config file section and perform the actions it describes.

    Args:
        config:         ConfigParser to read the section from.
        section:        string section name to read from the ConfigParser.
        config_path:    string path to the read config file.
        verbose:        boolean, True to output verbose status to stdout.
            Defaults to False.
        gpg_home:       string path for the location of the GPG home directory
            to use. May be None to use the default location for the machine's
            GPG implementation (typically ~/gnupg). Defaults to None.

    Raises:
        OSError:    if the source path given in the section does not exist.
    """
    # Extract fields from the section (and write-back any missing).
    if not config.has_option(section, SRC_KEY):
        config.set(section, SRC_KEY, section)
    pipeline_src = resolve_relative_path(config.get(section, SRC_KEY), config_path)
    pipeline_dest = resolve_relative_path(config.get(section, DEST_KEY), config_path)
    archive = config.getboolean(section, ARCHIVE_KEY)
    compress = config.getboolean(section, COMPRESS_KEY)
    encrypt = config.getboolean(section, ENCRYPT_KEY)

    # Validate args.
    if not os.path.exists(pipeline_src):
        raise OSError("Source path %s does not exist." % (pipeline_src))
    if not os.path.exists(pipeline_dest):
        os.makedirs(pipeline_dest)
    if (compress or encrypt) and os.path.isdir(pipeline_src):
        archive = True

    # Perform backup pipeline.
    stage_src = pipeline_src
    if archive or compress or encrypt:
        tempdir = make_tempdir()

        if archive:
            stage_dest = get_out_filename(tempdir, stage_src, 'tar')
            archive_path(stage_dest, stage_src, verbose=verbose)
            stage_src = stage_dest

        if compress:
            stage_dest = get_out_filename(tempdir, stage_src, 'xz')
            compress_path(stage_dest, stage_src, verbose=verbose)
            stage_src = stage_dest

        if encrypt:
            stage_dest = get_out_filename(tempdir, stage_src, 'gpg')
            encrypt_path(stage_dest, stage_src, verbose=verbose, homedir=gpg_home)
            stage_src = stage_dest

    # Perform copy.
    copy_path(pipeline_dest, stage_src, verbose=verbose)

def main(argv=None):
    """Main method.

    Args:
        argv:   list of strings to pass through to the ArgumentParser. If None
            will pass through sys.argv instead. Defaults to None.

    Raises:
        OSError:    if the config file path given does not exist.
    """
    global _TEMPDIR
    # Handle command line.
    parser = argparse.ArgumentParser(description='A micro backup manager, '
                                     'designed to be lightly configurable, '
                                     'simple and unobtrusive. Useful for '
                                     'maintaining lightweight backups.')
    parser.add_argument('--config', metavar='PATH',
                        type=str, default='~/.backup_config',
                        help='The location of the backup config file to read. '
                        'Defaults to %(default)s')
    parser.add_argument('--gpg-home', metavar='PATH',
                        type=str, default=None,
                        help='The location of the GPG home directory to use if '
                        'encrypting data. Defaults to that of the machine\'s '
                        'GPG implementation (typically ~/gnupg).')
    parser.add_argument('--restore',
                        action='store_true', default=False,
                        help='Reverse the backup process to restore the local '
                        'file system from the backups at the given locations.')
    parser.add_argument('--retention', metavar='N',
                        type=int, default=1,
                        help='The number of copies of the backup to retain. '
                        'When this is exceeded, the oldest will be '
                        'removed. Defaults to %(default)s.')
    parser.add_argument('--verbose',
                        action='store_true', default=False,
                        help='Print additional output.')
    parser.add_argument('--version',
                        action='version', version='%(prog)s ' + __version__)
    args = parser.parse_args(args=argv)

    # Process command line.
    if args.restore:
        raise NotImplementedError('Restore functionality is not implemented.')
    if args.retention != 1:
        raise NotImplementedError('Retention functionality is not implemented')

    # Parse the config file.
    args.config = os.path.expanduser(args.config)
    if not os.path.isfile(args.config):
        raise OSError('Config file "%s" does not exist.' % (args.config))
    config = ConfigParser.SafeConfigParser(DEFAULTS)
    with open(args.config) as config_file:
        config.readfp(config_file)

    # Perform the backup.
    try:
        for section in config.sections():
            process_section(config, section, args.config, verbose=args.verbose,
                            gpg_home=args.gpg_home)
    finally:
        if _TEMPDIR:
            shutil.rmtree(_TEMPDIR)
            _TEMPDIR = None

# Entry point.
if __name__ == "__main__":
    main()
