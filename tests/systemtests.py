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
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
import test

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

    _BACKUP_BIN = os.path.join(sys.path[0], '..', 'backup.py')

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
            stdout = subprocess.check_output([self._BACKUP_BIN, '--config', cfg_file])
            self.assertEqual('', stdout)

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertTrue(os.path.isfile(out_file))
            self.assertEqual(in_file_hash, test.get_file_md5(in_file))
            self.assertEqual(in_file_hash, test.get_file_md5(out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)
