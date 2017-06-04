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

class _SystemTestData(object):
    def __init__(self, in_dir, in_dir_hash, out_dir, out_dir_hash):
        self.in_dir = in_dir
        self.in_dir_hash = in_dir_hash
        self.out_dir = out_dir
        self.out_dir_hash = out_dir_hash

class TestBackupSystem(unittest.TestCase):
    """System tests TestCase"""

    def _create_tempdir_structure(self, in_dirname, out_dirname):
        # Create temporary directory structure.
        tempdir = tempfile.mkdtemp()
        in_dir = os.path.join(tempdir, in_dirname)
        out_dir = os.path.join(tempdir, out_dirname)
        os.makedirs(in_dir)
        os.makedirs(out_dir)
        return tempdir, in_dir, out_dir

    def _create_single_file_test(self, in_filename, out_filename, cfg_dir,
                                 in_dir, out_dir, sections):
        # Create files within the input structure.
        in_file = os.path.join(in_dir, in_filename)
        out_file = os.path.join(out_dir, out_filename)
        test.create_ascii_file(in_file)

        # Create the config file for this structure.
        cfg_file = os.path.join(cfg_dir, 'simple.cfg')
        _write_config_file(cfg_file, sections)

        # Assert the starting state looks as we expect.
        self.assertTrue(os.path.isfile(cfg_file))
        self.assertTrue(os.path.isfile(in_file))
        self.assertFalse(os.path.exists(out_file))

        return in_file, out_file, cfg_file

    def _create_single_dir_test(self, in_dirname, out_dirname, cfg_dir,
                                in_dir, out_dir, sections):
        # Create files within the input structure.
        in_struct = os.path.join(in_dir, in_dirname)
        out_struct = os.path.join(out_dir, out_dirname)
        test.create_test_structure(in_struct)

        # Create the config file for this structure.
        cfg_file = os.path.join(cfg_dir, 'simple.cfg')
        _write_config_file(cfg_file, sections)

        # Assert the starting state looks as we expect.
        self.assertTrue(os.path.isfile(cfg_file))
        self.assertTrue(os.path.isdir(in_struct))
        self.assertFalse(os.path.exists(out_struct))

        return in_struct, out_struct, cfg_file

    def test_file_copy(self):
        """Most basic test of a single file backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_file, out_file, cfg_file = self._create_single_file_test(\
                'file.txt', 'file.txt', tempdir, in_dir, out_dir, \
                [_ConfigSection('input/file.txt', out_dir)])
            in_dir_hash = test.get_dir_md5(in_dir)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertTrue(os.path.isfile(out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)

    def test_file_copy_archive(self):
        """Basic test of a single file archive and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_file, out_file, cfg_file = self._create_single_file_test(\
                'file.txt', 'file.txt.tar', tempdir, in_dir, out_dir, \
                [_ConfigSection('input/file.txt', out_dir, archive='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)
            in_file_hash = test.get_file_md5(in_file)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertTrue(os.path.isfile(out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(tempdir, 'file.txt')
            backup.unarchive_path(tempdir, out_file)
            self.assertTrue(os.path.isfile(undo_out_file))
            self.assertEqual(in_file_hash, test.get_file_md5(undo_out_file))

        finally:
            shutil.rmtree(tempdir)

    def test_file_copy_compress(self):
        """Basic test of a single file compress and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_file, out_file, cfg_file = self._create_single_file_test(\
                'file.txt', 'file.txt.xz', tempdir, in_dir, out_dir, \
                [_ConfigSection('input/file.txt', out_dir, compress='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)
            in_file_hash = test.get_file_md5(in_file)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertTrue(os.path.isfile(out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(tempdir, 'file.txt')
            backup.uncompress_path(undo_out_file, out_file)
            self.assertTrue(os.path.isfile(undo_out_file))
            self.assertEqual(in_file_hash, test.get_file_md5(undo_out_file))

        finally:
            shutil.rmtree(tempdir)

    def test_file_copy_encrypt(self):
        """Basic test of a single file encrypt and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_file, out_file, cfg_file = self._create_single_file_test(\
                'file.txt', 'file.txt.gpg', tempdir, in_dir, out_dir, \
                [_ConfigSection('input/file.txt', out_dir, encrypt='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)
            in_file_hash = test.get_file_md5(in_file)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file, '--gpg-home', test.GPG_HOME])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertTrue(os.path.isfile(out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(tempdir, 'file.txt')
            backup.unencrypt_path(undo_out_file, out_file, homedir=test.GPG_HOME)
            self.assertTrue(os.path.isfile(undo_out_file))
            self.assertEqual(in_file_hash, test.get_file_md5(undo_out_file))

        finally:
            shutil.rmtree(tempdir)

    def test_file_copy_full_pipeline(self):
        """Basic test of a single file archive, compress, encrypt and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_file, out_file, cfg_file = self._create_single_file_test(\
                'file.txt', 'file.txt.tar.xz.gpg', tempdir, in_dir, out_dir, \
                [_ConfigSection('input/file.txt', out_dir, archive='yes',
                                compress='yes', encrypt='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)
            in_file_hash = test.get_file_md5(in_file)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file, '--gpg-home', test.GPG_HOME])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isfile(in_file))
            self.assertTrue(os.path.isfile(out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(tempdir, 'file.txt')
            backup.unencrypt_path(os.path.join(tempdir, 'file.txt.tar.xz'),
                                  out_file, homedir=test.GPG_HOME)
            backup.uncompress_path(os.path.join(tempdir, 'file.txt.tar'),
                                   os.path.join(tempdir, 'file.txt.tar.xz'))
            backup.unarchive_path(tempdir, os.path.join(tempdir, 'file.txt.tar'))
            self.assertTrue(os.path.isfile(undo_out_file))
            self.assertEqual(in_file_hash, test.get_file_md5(undo_out_file))

        finally:
            shutil.rmtree(tempdir)

    def test_dir_copy(self):
        """Most basic test of a single directory backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_struct, out_struct, cfg_file = self._create_single_dir_test(\
                'struct', 'struct', tempdir, in_dir, out_dir, \
                [_ConfigSection('input/struct', out_dir)])
            in_dir_hash = test.get_dir_md5(in_dir)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isdir(in_struct))
            self.assertTrue(os.path.isdir(out_struct))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)

    def test_dir_copy_archive(self):
        """Basic test of a single directory archive and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_struct, out_struct, cfg_file = self._create_single_dir_test(\
                'struct', 'struct.tar', tempdir, in_dir, tempdir, \
                [_ConfigSection('input/struct', tempdir, archive='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isdir(in_struct))
            self.assertTrue(os.path.isfile(out_struct))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(out_dir, 'struct')
            backup.unarchive_path(out_dir, out_struct)
            self.assertTrue(os.path.isdir(undo_out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)

    def test_dir_copy_compress(self):
        """Basic test of a single directory archive, compress and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_struct, out_struct, cfg_file = self._create_single_dir_test(\
                'struct', 'struct.tar.xz', tempdir, in_dir, tempdir, \
                [_ConfigSection('input/struct', tempdir, archive='yes',
                                compress='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isdir(in_struct))
            self.assertTrue(os.path.isfile(out_struct))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(out_dir, 'struct')
            backup.uncompress_path(os.path.join(tempdir, 'struct.tar'), out_struct)
            backup.unarchive_path(out_dir, os.path.join(tempdir, 'struct.tar'))
            self.assertTrue(os.path.isdir(undo_out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)

    def test_dir_copy_encrypt(self):
        """Basic test of a single directory archive, encrypt and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_struct, out_struct, cfg_file = self._create_single_dir_test(\
                'struct', 'struct.tar.gpg', tempdir, in_dir, tempdir, \
                [_ConfigSection('input/struct', tempdir, archive='yes',
                                encrypt='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file, '--gpg-home', test.GPG_HOME])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isdir(in_struct))
            self.assertTrue(os.path.isfile(out_struct))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(out_dir, 'struct')
            backup.unencrypt_path(os.path.join(tempdir, 'struct.tar'), out_struct,
                                  homedir=test.GPG_HOME)
            backup.unarchive_path(out_dir, os.path.join(tempdir, 'struct.tar'))
            self.assertTrue(os.path.isdir(undo_out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)

    def test_dir_copy_full_pipeline(self):
        """Basic test of a single directory archive, encrypt and backup."""
        try:
            # Setup the test state.
            tempdir, in_dir, out_dir = self._create_tempdir_structure('input', \
                'output')
            in_struct, out_struct, cfg_file = self._create_single_dir_test(\
                'struct', 'struct.tar.xz.gpg', tempdir, in_dir, tempdir, \
                [_ConfigSection('input/struct', tempdir, archive='yes',
                                compress='yes', encrypt='yes')])
            in_dir_hash = test.get_dir_md5(in_dir)

            # Run backup.
            with redir_stdstreams() as (stdout, stderr):
                backup.main(['--config', cfg_file, '--gpg-home', test.GPG_HOME])
            self.assertEqual('', stdout.getvalue().strip())
            self.assertEqual('', stderr.getvalue().strip())

            # Assert the output state looks as we expect.
            self.assertTrue(os.path.isdir(in_struct))
            self.assertTrue(os.path.isfile(out_struct))
            self.assertEqual(in_dir_hash, test.get_dir_md5(in_dir))
            undo_out_file = os.path.join(out_dir, 'struct')
            backup.unencrypt_path(os.path.join(tempdir, 'struct.tar.xz'),
                                  out_struct, homedir=test.GPG_HOME)
            backup.uncompress_path(os.path.join(tempdir, 'struct.tar'),
                                   os.path.join(tempdir, 'struct.tar.xz'))
            backup.unarchive_path(out_dir, os.path.join(tempdir, 'struct.tar'))
            self.assertTrue(os.path.isdir(undo_out_file))
            self.assertEqual(in_dir_hash, test.get_dir_md5(out_dir))

        finally:
            shutil.rmtree(tempdir)
