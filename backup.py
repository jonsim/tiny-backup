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
    """Retrieves a temporary directory, creating it if necessary.

    Returns:    string path to a temporary directory.
    """
    global _TEMPDIR
    if not _TEMPDIR:
        _TEMPDIR = tempfile.mkdtemp()
    return _TEMPDIR

def archive_path(dest, src, excludes=[], verbose=False):
    assert dest and not os.path.isdir(dest) and dest.endswith('.tar')
    assert src and os.path.exists(src)
    cmd = ['tar']
    cmd.append('--create')
    if verbose:
        print '\narchive_path(%s, %s)' % (dest, src)
        cmd.append('-v')
    if excludes:
        for exclude in excludes:
            cmd.append('--exclude=%s' % (exclude))
    cmd.append('--file')
    cmd.append(dest)
    cmd.append('--directory')
    cmd.append(os.path.dirname(src))
    cmd.append(os.path.basename(src))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as cpe:
        raise OSError('tar command "%s" exitted with "%s"' %
                      (cpe.cmd, cpe.output))

def unarchive_path(dest, src, verbose=False):
    assert dest and os.path.isdir(dest)
    assert src and os.path.isfile(src) and src.endswith('.tar')
    cmd = ['tar']
    cmd.append('--extract')
    if verbose:
        print '\nunarchive_path(%s, %s)' % (dest, src)
        cmd.append('-v')
    cmd.append('--file')
    cmd.append(src)
    cmd.append('--directory')
    cmd.append(dest)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as cpe:
        raise OSError('tar command "%s" exitted with "%s"' %
                      (cpe.cmd, cpe.output))

def compress_path(dest, src, verbose=False):
    assert src and os.path.exists(src)
    cmd = ['xz']
    if verbose:
        print '\ncompress_path(%s, %s)' % (dest, src)
        cmd.append('-v')
    cmd.append('--keep')
    cmd.append('--stdout')
    cmd.append('--compress')
    cmd.append(src)
    try:
        dest_file = open(dest, 'w')
        subprocess.check_call(cmd, stdout=dest_file)
        dest_file.close()
    except subprocess.CalledProcessError as cpe:
        raise OSError('xz command "%s" exitted with "%s"' %
                      (cpe.cmd, cpe.output))

def uncompress_path(dest, src, verbose=False):
    assert src and os.path.isfile(src) and src.endswith('.xz')
    cmd = ['xz']
    if verbose:
        print '\nuncompress_path(%s, %s)' % (dest, src)
        cmd.append('-v')
    cmd.append('--keep')
    cmd.append('--stdout')
    cmd.append('--decompress')
    cmd.append(src)
    try:
        dest_file = open(dest, 'w')
        subprocess.check_call(cmd, stdout=dest_file)
        dest_file.close()
    except subprocess.CalledProcessError as cpe:
        raise OSError('xz command "%s" exitted with "%s"' %
                      (cpe.cmd, cpe.output))

def encrypt_path(dest, src, verbose=False):
    assert dest and not os.path.isdir(dest) and dest.endswith('.gpg')
    assert src and os.path.isfile(src)
    cmd = ['gpg']
    if verbose:
        print '\nencrypt_path(%s, %s)' % (dest, src)
        cmd.append('-v')
    cmd.append('--default-recipient-self')
    cmd.append('--output')
    cmd.append(dest)
    cmd.append('--encrypt')
    cmd.append(src)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as cpe:
        raise OSError('gpg command "%s" exitted with "%s"' %
                      (cpe.cmd, cpe.output))

def unencrypt_path(dest, src, verbose=False):
    assert dest and not os.path.isdir(dest)
    assert src and os.path.isfile(src) and src.endswith('.gpg')
    cmd = ['gpg']
    if verbose:
        print '\nunencrypt_path(%s, %s)' % (dest, src)
        cmd.append('-v')
    cmd.append('--default-recipient-self')
    cmd.append('--output')
    cmd.append(dest)
    cmd.append('--decrypt')
    cmd.append(src)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as cpe:
        raise OSError('gpg command "%s" exitted with "%s"' %
                      (cpe.cmd, cpe.output))

def copy_path(dest, src, excludes=[], verbose=False):
    assert dest and src
    cmd = ['rsync']
    if verbose:
        print '\ncopy_path(%s, %s)' % (dest, src)
        cmd.append('-v')            # Set verbosity (-v)
    cmd.append('--archive')         # Preserve metadata (-a)
    cmd.append('--delete')          # Delete extra files
    cmd.append('--compress')        # Compress xfer data (-z)
    cmd.append('--protect-args')    # Preserve whitespace (-s)
    if excludes:
        for exclude in excludes:
            cmd.append('--filter=exclude_%s' % (exclude))
    cmd.append(src)
    cmd.append(dest)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as cpe:
        raise OSError('rsync command "%s" exitted with "%s"' %
                      (cpe.cmd, cpe.output))

def resolve_relative_path(path, config_path):
    if os.path.isabs(path):
        return path
    return os.path.join(os.path.dirname(config_path), path)

def get_pipeline_stage_output(pipeline_dest, src, end_of_pipeline, extension):
    # If not the end of the pipeline make a temp location for the output.
    return os.path.join(pipeline_dest if end_of_pipeline else make_tempdir(),
        '%s.%s' % (os.path.basename(src), extension))

def process_section(config, section, config_path, verbose=False):
    # Extract fields from the section (and write-back any missing).
    if not config.has_option(section, SRC_KEY):
        config.set(section, SRC_KEY, section)
    pipeline_src = resolve_relative_path(config.get(section, SRC_KEY), config_path)
    pipeline_dest = resolve_relative_path(config.get(section, DEST_KEY), config_path)
    archive = config.getboolean(section, ARCHIVE_KEY)
    compress = config.getboolean(section, COMPRESS_KEY)
    encrypt = config.getboolean(section, ENCRYPT_KEY)
    #print dest, src, archive, compress, encrypt

    # Validate args.
    if not os.path.exists(pipeline_src):
        raise Exception("Source path %s does not exist." % (pipeline_src))
    if not os.path.exists(pipeline_dest):
        os.makedirs(pipeline_dest)
    if (compress or encrypt) and os.path.isdir(pipeline_src):
        archive = True

    # Perform backup.
    if archive or compress or encrypt:
        # Perform pipeline.
        stage_src = pipeline_src
        if archive:
            stage_dest = get_pipeline_stage_output(pipeline_dest, stage_src,
                                                   not (compress or encrypt), 'tar')
            archive_path(stage_dest, stage_src, verbose=verbose)
            stage_src = stage_dest

        if compress:
            stage_dest = get_pipeline_stage_output(pipeline_dest, stage_src,
                                                   not encrypt, 'xz')
            compress_path(stage_dest, stage_src, verbose=verbose)
            stage_src = stage_dest

        if encrypt:
            stage_dest = get_pipeline_stage_output(pipeline_dest, stage_src,
                                                   True, 'gpg')
            encrypt_path(stage_dest, stage_src, verbose=verbose)
            stage_src = stage_dest
    else:
        # Perform copy.
        copy_path(pipeline_dest, pipeline_src, verbose=verbose)

def main():
    """Main method."""
    # Handle command line.
    parser = argparse.ArgumentParser(description='A micro backup manager, '
                                     'designed to be lightly configurable, '
                                     'simple and unobtrusive. Useful for '
                                     'maintaining lightweight backups.')
    parser.add_argument('--config', metavar='PATH',
                        type=str, default='~/.backup_config',
                        help='The location of the backup config file to read. '
                        'Defaults to %(default)s')
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
    args = parser.parse_args()

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
            process_section(config, section, args.config, args.verbose)
    finally:
        if _TEMPDIR:
            shutil.rmtree(_TEMPDIR)

# Entry point.
if __name__ == "__main__":
    main()
