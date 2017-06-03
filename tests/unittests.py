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
import subprocess
import sys
import tempfile
import unittest
# To avoid having to make the parent directory a module just amend PYTHONPATH.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import backup

def _create_ascii_file(path, kb_size=16):
    """Creates an ASCII file.

    Args:
        path:       string path for the file to be written to.
        kb_size:    int (approximate) size, in KB, of the file to create.
    """
    assert not os.path.exists(path)
    with open(path, 'w') as out_file:
        num = 0
        file_size = 0
        while (file_size / 1024) < kb_size:
            line = ' '.join(["%04d" % (i) for i in range(num * 16, (num + 1) * 16)]) + '\n'
            out_file.write(line)
            num += 1
            file_size += len(line)

def _create_binary_file(path, kb_size=16):
    """Creates a binary file.

    Args:
        path:       string path for the file to be written to.
        kb_size:    int (approximate) size, in KB, of the file to create.
    """
    assert not os.path.exists(path)
    with open(path, 'wb') as out_file:
        out_file.write(bytearray(range(256) * 4 * kb_size))

def _create_test_dir(path):
    """Creates a test directory and populates it full of files.

    Args:
        path:       string path for the directory to be created at.
    """
    assert not os.path.exists(path)
    os.makedirs(path)
    _create_ascii_file(os.path.join(path, 'file.txt'), 8)
    _create_ascii_file(os.path.join(path, 'file.log'), 24)
    _create_binary_file(os.path.join(path, 'file.bin'), 16)

def _create_test_structure(path):
    """Creates a test directory structure with files and directories.

    Args:
        path:       string path for the directory structure to be created at.
    """
    assert not os.path.exists(path)
    os.makedirs(path)
    _create_test_dir(os.path.join(path, 'test_dir1'))
    _create_test_dir(os.path.join(path, 'test_dir1', 'test_subdir'))
    _create_test_dir(os.path.join(path, 'test_dir2'))
    _create_ascii_file(os.path.join(path, 'root_file.txt'))
    _create_binary_file(os.path.join(path, 'root_file.bin'))

def _get_file_md5(path):
    """Retrieves the md5sum of a file's contents.

    Args:
        path:   string path of the file to hash.

    Returns:
        string md5sum hash.
    """
    import hashlib
    hash_md5 = hashlib.md5()
    with open(path, 'rb') as in_file:
        hash_md5.update(in_file.read())
    return hash_md5.hexdigest()

def _get_dir_md5(path):
    """Retrieves the md5sum for a directory and all its contents.

    Args:
        path:   string path of the directory to hash.

    Returns:
        string md5sum hash.
    """
    import hashlib
    hash_md5 = hashlib.md5()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        files.sort()
        rel_root = '.' + root[len(path):]
        hash_md5.update(rel_root)
        for directory in dirs:
            hash_md5.update(directory)
        for sub_file in files:
            with open(os.path.join(root, sub_file), 'rb') as in_file:
                hash_md5.update(in_file.read())
    return hash_md5.hexdigest()

def _get_file_type(path):
    """Determines the file type of a path as given by the 'file' command.

    Args:
        path:   string path of the file whose type will be determined.

    Returns:
        string file type.
    """
    return subprocess.check_output(['file', '--brief', path]).strip()

class TestBackupMethods(unittest.TestCase):
    """Test runner method"""

    _FILE_TYPE_ASCII = 'ASCII text'
    _FILE_TYPE_BINARY = 'raw G3 data, byte-padded'
    _FILE_TYPE_DIR = 'directory'
    _FILE_TYPE_TAR = 'POSIX tar archive (GNU)'
    _FILE_TYPE_XZ = 'XZ compressed data'
    _FILE_TYPE_GPG = 'PGP RSA encrypted session key - keyid: A294AFC5 ' \
                     'A32F6F37 RSA (Encrypt or Sign) 1024b .'

    def _assert_file_processing(self, processing_func, unprocessing_func,
                                processed_file_type, input_filename,
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
                _create_ascii_file(test_input)
                input_file_type = self._FILE_TYPE_ASCII
            else:
                _create_binary_file(test_input)
                input_file_type = self._FILE_TYPE_BINARY

            # Assert the starting state looks as we expect.
            self.assertTrue(os.path.isfile(test_input))
            self.assertFalse(os.path.exists(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(input_file_type, _get_file_type(test_input))
            test_input_hash = _get_file_md5(test_input)

            # Perform the processing operation on the file.
            processing_func(test_processed, test_input)

            # Assert the processed state looks as we expect.
            self.assertTrue(os.path.isfile(test_input))
            self.assertTrue(os.path.isfile(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(input_file_type, _get_file_type(test_input))
            self.assertEqual(test_input_hash, _get_file_md5(test_input))
            self.assertEqual(processed_file_type, _get_file_type(test_processed))
            test_processed_hash = _get_file_md5(test_processed)
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
            self.assertEqual(input_file_type, _get_file_type(test_output))
            self.assertEqual(test_input_hash, _get_file_md5(test_output))
            self.assertEqual(processed_file_type, _get_file_type(test_processed))
            self.assertEqual(test_processed_hash, _get_file_md5(test_processed))

        finally:
            shutil.rmtree(tempdir)

    def _assert_dir_processing(self, processing_func, unprocessing_func,
                               processed_file_type, input_dirname,
                               processed_dirname, output_dirname,
                               output_is_dir=False, processed_is_dir=False,
                               processed_is_same=False):
        try:
            tempdir = tempfile.mkdtemp()
            out_dir = os.path.join(tempdir, 'output')
            os.makedirs(out_dir)

            test_input = os.path.join(tempdir, input_dirname)
            test_processed = os.path.join(tempdir, processed_dirname)
            test_output = os.path.join(out_dir, output_dirname)

            # Create the structure.
            _create_test_structure(test_input)

            # Assert the starting state looks as we expect.
            self.assertTrue(os.path.isdir(test_input))
            self.assertFalse(os.path.exists(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(self._FILE_TYPE_DIR, _get_file_type(test_input))
            test_input_hash = _get_dir_md5(test_input)

            # Perform the processing operation on the directory.
            processing_func(test_processed, test_input)

            # Assert the processed state looks as we expect.
            self.assertTrue(os.path.isdir(test_input))
            if processed_is_dir:
                self.assertTrue(os.path.isdir(test_processed))
            else:
                self.assertTrue(os.path.isfile(test_processed))
            self.assertFalse(os.path.exists(test_output))
            self.assertEqual(self._FILE_TYPE_DIR, _get_file_type(test_input))
            self.assertEqual(test_input_hash, _get_dir_md5(test_input))
            self.assertEqual(processed_file_type, _get_file_type(test_processed))
            if processed_is_dir:
                test_processed_hash = _get_dir_md5(test_processed)
            else:
                test_processed_hash = _get_file_md5(test_processed)
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
            self.assertEqual(self._FILE_TYPE_DIR, _get_file_type(test_output))
            self.assertEqual(test_input_hash, _get_dir_md5(test_output))
            self.assertEqual(processed_file_type, _get_file_type(test_processed))
            if processed_is_dir:
                self.assertEqual(test_processed_hash, _get_dir_md5(test_processed))
            else:
                self.assertEqual(test_processed_hash, _get_file_md5(test_processed))

        finally:
            shutil.rmtree(tempdir)


    def test_archive_path_ascii_file(self):
        """Test the archive methods with an ASCII file path argument."""
        self._assert_file_processing(backup.archive_path, backup.unarchive_path,
                                     self._FILE_TYPE_TAR, 'testfile.txt',
                                     'testfile.tar', 'testfile.txt', True,
                                     output_is_dir=True)

    def test_archive_path_binary_file(self):
        """Test the archive methods with a binary file path argument."""
        self._assert_file_processing(backup.archive_path, backup.unarchive_path,
                                     self._FILE_TYPE_TAR, 'testfile.bin',
                                     'bin.tar', 'testfile.bin', False,
                                     output_is_dir=True)

    def test_archive_path_directory(self):
        """Test the archive methods with a directory path argument."""
        self._assert_dir_processing(backup.archive_path, backup.unarchive_path,
                                    self._FILE_TYPE_TAR, 'struct', 'dir.tar',
                                    'struct', output_is_dir=True)

    def test_compress_path_ascii_file(self):
        """Test the compress methods with an ASCII file path argument."""
        self._assert_file_processing(backup.compress_path, backup.uncompress_path,
                                     self._FILE_TYPE_XZ, 'testfile.txt',
                                     'testfile.xz', 'testfile.txt', True)

    def test_compress_path_binary_file(self):
        """Test the compress methods with a binary file path argument."""
        self._assert_file_processing(backup.compress_path, backup.uncompress_path,
                                     self._FILE_TYPE_XZ, 'testfile.bin',
                                     'compressed.xz', 'testfile.bin', False)

    def test_encrypt_path_ascii_file(self):
        """Test the encrypt methods with an ASCII file path argument."""
        # Wrap the backup.xcrypt_path functions so we can inject the unittesting
        # homedir and use it's key (which should never be used for anything as
        # it's completely insecure) rather than the keys of the current user.
        test_home = os.path.join(sys.path[0], 'gpg-test-homedir')
        encrypt = lambda d, s: backup.encrypt_path(d, s, homedir=test_home)
        unencrypt = lambda d, s: backup.unencrypt_path(d, s, homedir=test_home)
        self._assert_file_processing(encrypt, unencrypt,
                                     self._FILE_TYPE_GPG, 'testfile.txt',
                                     'testfile.gpg', 'testfile.txt', True)

    def test_encrypt_path_binary_file(self):
        """Test the encrypt methods with a binary file path argument."""
        # Wrap the backup.xcrypt_path functions so we can inject the unittesting
        # homedir and use it's key (which should never be used for anything as
        # it's completely insecure) rather than the keys of the current user.
        test_home = os.path.join(sys.path[0], 'gpg-test-homedir')
        encrypt = lambda d, s: backup.encrypt_path(d, s, homedir=test_home)
        unencrypt = lambda d, s: backup.unencrypt_path(d, s, homedir=test_home)
        self._assert_file_processing(encrypt, unencrypt,
                                     self._FILE_TYPE_GPG, 'testfile.bin',
                                     'encrypted.gpg', 'testfile.bin', False)

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
                                    'copied', 'struct', processed_is_dir=True,
                                    processed_is_same=True)
