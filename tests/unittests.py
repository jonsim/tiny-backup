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
Unit tests for tiny-backup.

Maintained at https://github.com/jonsim/tiny-backup
"""
import os
import shutil
import sys
import tempfile
import unittest
# To avoid having to make the parent directory a module just amend PYTHONPATH.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import backup
import test

class TestBackupMethods(unittest.TestCase):
    """Unit tests TestCase"""

    _FILE_TYPE_ASCII = 'ASCII text'
    _FILE_TYPE_BINARY = 'raw G3 data, byte-padded'
    _FILE_TYPE_DATA = 'data'
    _FILE_TYPE_DIR = 'directory'
    _FILE_TYPE_GPG = 'PGP RSA encrypted session key - keyid: A294AFC5 ' \
                     'A32F6F37 RSA (Encrypt or Sign) 1024b .'
    _FILE_TYPE_TAR = 'POSIX tar archive (GNU)'
    _FILE_TYPE_XZ = 'XZ compressed data'

    def _assert_file_processing(self, processing_func, unprocessing_func,
                                processed_file_types, input_filename,
                                processed_filename, output_filename, is_ascii,
                                output_is_dir=False, processed_is_same=False):
        try:
            tempdir = tempfile.mkdtemp()
            out_dir = os.path.join(tempdir, 'output')
            os.makedirs(out_dir)

            test_input = os.path.join(tempdir, input_filename)
            test_processed = os.path.join(tempdir, processed_filename)
            test_output = os.path.join(out_dir, output_filename)

            # Create the file.
            if is_ascii:
                test.create_ascii_file(test_input)
                input_file_type = self._FILE_TYPE_ASCII
            else:
                test.create_binary_file(test_input)
                input_file_type = self._FILE_TYPE_BINARY

            # Assert the starting state looks as we expect.
            self.assertTrue(os.path.isfile(test_input))
            self.assertFalse(os.path.exists(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(input_file_type, test.get_file_type(test_input))
            test_input_hash = test.get_file_md5(test_input)

            # Perform the processing operation on the file.
            processing_func(test_processed, test_input)

            # Assert the processed state looks as we expect.
            self.assertTrue(os.path.isfile(test_input))
            self.assertTrue(os.path.isfile(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(input_file_type, test.get_file_type(test_input))
            self.assertEqual(test_input_hash, test.get_file_md5(test_input))
            self.assertIn(test.get_file_type(test_processed), processed_file_types)
            test_processed_hash = test.get_file_md5(test_processed)
            self.assertEqual(32, len(test_processed_hash))
            if processed_is_same:
                self.assertEqual(test_input_hash, test_processed_hash)
            else:
                self.assertNotEqual(test_input_hash, test_processed_hash)

            # Delete the file (so we can check it doesn't get recreated).
            os.remove(test_input)
            self.assertFalse(os.path.exists(test_input))

            # Perform the reverse processing operation on the file.
            unprocessing_func(out_dir if output_is_dir else test_output,
                              test_processed)

            # Assert the unprocessed state looks as we expect.
            self.assertFalse(os.path.exists(test_input))
            self.assertTrue(os.path.isfile(test_processed))
            self.assertTrue(os.path.isfile(test_output))
            self.assertEqual(input_file_type, test.get_file_type(test_output))
            self.assertEqual(test_input_hash, test.get_file_md5(test_output))
            self.assertIn(test.get_file_type(test_processed), processed_file_types)
            self.assertEqual(test_processed_hash, test.get_file_md5(test_processed))

        finally:
            shutil.rmtree(tempdir)

    def _assert_dir_processing(self, processing_func, unprocessing_func,
                               processed_file_types, input_dirname,
                               processed_dirname, output_dirname,
                               output_is_dir=False, processed_is_dir=False,
                               processed_is_same=False):
        """
        Creates a directory structure in an 'input' directory. Then performs a
        generic 'processing function' to mutate this input directory structure
        into something in a 'processed' directory. Finally it performs a generic
        'unprocessing function' to un-mutate this processed directory into a
        directory structure in an 'output' directory. Asserts throughout that
        the contents of input and output directories is the same, and the
        processed directory state is as expected.

        Args:
            processing_func:        A callable which has a signature like
                processing_func(dest, src) where dest is a path to the processed
                output and src is a path to the input for processing.
            unprocessing_func:      A callable which has a signature like
                unprocessing_func(dest, src) where dest is a path to the
                unprocessed output and src is a path to the input for
                unprocessing.
            processed_file_types:   A list of strings describing the acceptable
                file types of the processed output.
            input_dirname:          string name of the input dir structure.
            processed_dirname:      string name of the processed dir structure.
            output_dirname:         string name of the unprocessed dir structure
            output_is_dir:          boolean, True if the output is a directory.
            processed_is_dir:       boolean, True if the processed output is a
                directory.
            processed_is_same:      boolean, True if the processed output is the
                same as the input.
        """
        try:
            tempdir = tempfile.mkdtemp()
            in_dir = os.path.join(tempdir, 'input')
            prc_dir = os.path.join(tempdir, 'processed')
            out_dir = os.path.join(tempdir, 'output')
            os.makedirs(in_dir)
            os.makedirs(prc_dir)
            os.makedirs(out_dir)

            test_input = os.path.join(in_dir, input_dirname)
            test_processed = os.path.join(prc_dir, processed_dirname)
            test_output = os.path.join(out_dir, output_dirname)

            # Create the structure.
            test.create_test_structure(test_input)

            # Assert the starting state looks as we expect.
            self.assertTrue(os.path.isdir(test_input))
            self.assertFalse(os.path.exists(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(self._FILE_TYPE_DIR, test.get_file_type(test_input))
            test_input_hash = test.get_dir_md5(test_input)

            # Perform the processing operation on the directory.
            processing_func(prc_dir if processed_is_dir else test_processed,
                            test_input)

            # Assert the processed state looks as we expect.
            self.assertTrue(os.path.isdir(test_input))
            if processed_is_dir:
                self.assertTrue(os.path.isdir(test_processed))
            else:
                self.assertTrue(os.path.isfile(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(self._FILE_TYPE_DIR, test.get_file_type(test_input))
            self.assertEqual(test_input_hash, test.get_dir_md5(test_input))
            self.assertIn(test.get_file_type(test_processed), processed_file_types)
            if processed_is_dir:
                test_processed_hash = test.get_dir_md5(test_processed)
            else:
                test_processed_hash = test.get_file_md5(test_processed)
            self.assertEqual(32, len(test_processed_hash))
            if processed_is_same:
                self.assertEqual(test_input_hash, test_processed_hash)
            else:
                self.assertNotEqual(test_input_hash, test_processed_hash)

            # Delete the struct (so we can check it doesn't get recreated).
            shutil.rmtree(test_input)
            self.assertFalse(os.path.exists(test_input))

            # Perform the reverse processing operation on the file.
            unprocessing_func(out_dir if output_is_dir else test_output,
                              test_processed)

            # Assert the unprocessed state looks as we expect.
            self.assertFalse(os.path.exists(test_input))
            if processed_is_dir:
                self.assertTrue(os.path.isdir(test_processed))
            else:
                self.assertTrue(os.path.isfile(test_processed))
            self.assertTrue(os.path.isdir(test_output))
            self.assertEqual(self._FILE_TYPE_DIR, test.get_file_type(test_output))
            self.assertEqual(test_input_hash, test.get_dir_md5(test_output))
            self.assertIn(test.get_file_type(test_processed), processed_file_types)
            if processed_is_dir:
                self.assertEqual(test_processed_hash, test.get_dir_md5(test_processed))
            else:
                self.assertEqual(test_processed_hash, test.get_file_md5(test_processed))

        finally:
            shutil.rmtree(tempdir)


    def test_archive_path_ascii_file(self):
        """Test the archive methods with an ASCII file path argument."""
        self._assert_file_processing(backup.archive_path, backup.unarchive_path,
                                     [self._FILE_TYPE_TAR], 'testfile.txt',
                                     'testfile.tar', 'testfile.txt', True,
                                     output_is_dir=True)

    def test_archive_path_binary_file(self):
        """Test the archive methods with a binary file path argument."""
        self._assert_file_processing(backup.archive_path, backup.unarchive_path,
                                     [self._FILE_TYPE_TAR], 'testfile.bin',
                                     'bin.tar', 'testfile.bin', False,
                                     output_is_dir=True)

    def test_archive_path_directory(self):
        """Test the archive methods with a directory path argument."""
        self._assert_dir_processing(backup.archive_path, backup.unarchive_path,
                                    [self._FILE_TYPE_TAR], 'struct', 'dir.tar',
                                    'struct', output_is_dir=True)

    def test_compress_path_ascii_file(self):
        """Test the compress methods with an ASCII file path argument."""
        self._assert_file_processing(backup.compress_path, backup.uncompress_path,
                                     [self._FILE_TYPE_XZ], 'testfile.txt',
                                     'testfile.xz', 'testfile.txt', True)

    def test_compress_path_binary_file(self):
        """Test the compress methods with a binary file path argument."""
        self._assert_file_processing(backup.compress_path, backup.uncompress_path,
                                     [self._FILE_TYPE_XZ], 'testfile.bin',
                                     'compressed.xz', 'testfile.bin', False)

    def test_encrypt_path_ascii_file(self):
        """Test the encrypt methods with an ASCII file path argument."""
        # Wrap the backup.xcrypt_path functions so we can inject the unittesting
        # homedir and use it's key (which should never be used for anything as
        # it's completely insecure) rather than the keys of the current user.
        encrypt = lambda d, s: backup.encrypt_path(d, s, homedir=test.GPG_HOME)
        unencrypt = lambda d, s: backup.unencrypt_path(d, s, homedir=test.GPG_HOME)
        self._assert_file_processing(encrypt, unencrypt,
                                     [self._FILE_TYPE_GPG, self._FILE_TYPE_DATA],
                                     'testfile.txt', 'testfile.gpg',
                                     'testfile.txt', True)

    def test_encrypt_path_binary_file(self):
        """Test the encrypt methods with a binary file path argument."""
        # Wrap the backup.xcrypt_path functions so we can inject the unittesting
        # homedir and use it's key (which should never be used for anything as
        # it's completely insecure) rather than the keys of the current user.
        encrypt = lambda d, s: backup.encrypt_path(d, s, homedir=test.GPG_HOME)
        unencrypt = lambda d, s: backup.unencrypt_path(d, s, homedir=test.GPG_HOME)
        self._assert_file_processing(encrypt, unencrypt,
                                     [self._FILE_TYPE_GPG, self._FILE_TYPE_DATA],
                                     'testfile.bin', 'encrypted.gpg',
                                     'testfile.bin', False)

    def test_copy_path_ascii_file(self):
        """Test the copy methods with an ASCII file path argument."""
        self._assert_file_processing(backup.copy_path, backup.copy_path,
                                     self._FILE_TYPE_ASCII, 'original.txt',
                                     'first.txt', 'second.txt', True,
                                     processed_is_same=True)

    def test_copy_path_binary_file(self):
        """Test the copy methods with a binary file path argument."""
        self._assert_file_processing(backup.copy_path, backup.copy_path,
                                     self._FILE_TYPE_BINARY, 'original.bin',
                                     'copied.bin', 'original.bin', False,
                                     processed_is_same=True)

    def test_copy_path_directory(self):
        """Test the copy methods with a directory path argument."""
        self._assert_dir_processing(backup.copy_path, backup.copy_path,
                                    self._FILE_TYPE_DIR, 'struct',
                                    'struct', 'struct', processed_is_dir=True,
                                    output_is_dir=True, processed_is_same=True)

    def test_resolve_relative_path(self):
        """Test backup.resolve_relative_path"""
        root_path = '/root/config.cfg'
        abs_path = '/some/path'
        rel_path = 'relative/path'
        self.assertTrue(os.path.isabs(root_path))
        self.assertTrue(os.path.isabs(abs_path))
        self.assertFalse(os.path.isabs(rel_path))
        self.assertEqual(abs_path,
                         backup.resolve_relative_path(abs_path, root_path))
        self.assertEqual('/root/relative/path',
                         backup.resolve_relative_path(rel_path, root_path))

    def test_get_out_filename(self):
        """Test backup.get_out_filename"""
        base_dir = '/root/dir'
        src_file = '/some/filename'
        out_file1 = backup.get_out_filename(base_dir, src_file, 'txt')
        out_file2 = backup.get_out_filename(src_file, base_dir, 'x')
        self.assertEqual('/root/dir/filename.txt', out_file1)
        self.assertEqual('/some/filename/dir.x', out_file2)
