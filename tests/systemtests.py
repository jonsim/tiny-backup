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
System tests for tiny-backup.

Maintained at https://github.com/jonsim/tiny-backup
"""
import contextlib
import os
import shutil
import sys
import tempfile
import unittest
# To avoid having to make the parent directory a module just amend PYTHONPATH.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import backup
import test

@contextlib.contextmanager
def redir_stdstreams():
    """
    Context manager which redirects stdout and stderr for its duration and
    yields the newly redirected versions.

    This is taken from https://stackoverflow.com/a/17981937

    Yields:
        stdout: redirected stdout (which will be equivalent to sys.stdout within
            the scope of this context manager).
        stderr: redirected stderr (which will be equivalent to sys.stderr within
            the scope of this context manager).
    """
    import StringIO
    new_stdout, new_stderr = StringIO.StringIO(), StringIO.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_stdout, new_stderr
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

class _ConfigSection(object):
    def __init__(self, section, dest, src=None, archive=None, compress=None,
                 encrypt=None):
        self.section = section
        self.dest = dest
        self.src = src
        self.archive = archive
        self.compress = compress
        self.encrypt = encrypt

def _write_config_file(config_path, sections):
    with open(config_path, 'w') as config_file:
        for section in sections:
            config_file.write('[%s]\n' % (section.section))
            if section.src:
                config_file.write('src = %s\n' % (section.src))
            config_file.write('dest = %s\n' % (section.dest))
            if section.archive:
                config_file.write('archive = %s\n' % (section.archive))
            if section.compress:
                config_file.write('compress = %s\n' % (section.compress))
            if section.encrypt:
                config_file.write('encrypt = %s\n' % (section.encrypt))
            config_file.write('\n')

class TestBackupSystem(unittest.TestCase):
    """System tests TestCase"""

    def test_single_file(self):
        """Most basic test of a single file backup."""
        try:
            # Create temporary directory structure.
            tempdir = tempfile.mkdtemp()
            in_dir = os.path.join(tempdir, 'input')
            out_dir = os.path.join(tempdir, 'output')
            os.makedirs(in_dir)
            os.makedirs(out_dir)

            # Create files within the input structure.
            in_file = os.path.join(in_dir, 'file.txt')
            out_file = os.path.join(out_dir, 'file.txt')
            test.create_ascii_file(in_file)

            # Create the config file for this structure.
            cfg_file = os.path.join(tempdir, 'simple.cfg')
            _write_config_file(cfg_file, \
                [_ConfigSection('input/file.txt', out_dir)])

            # Assert the starting state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertFalse(os.path.exists(out_file))
            in_file_hash = test.get_file_md5(in_file)
            in_dir_hash = test.get_dir_md5(in_dir)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file])
            stdout_str = stdout.getvalue().strip()
            stderr_str = stderr.getvalue().strip()
            self.assertEqual('', stdout_str)
            self.assertEqual('', stderr_str)

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertTrue(os.path.isfile(out_file))
            self.assertEqual(in_file_hash, test.get_file_md5(in_file))
            self.assertEqual(in_file_hash, test.get_file_md5(out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)
