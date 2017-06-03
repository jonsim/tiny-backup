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
import tempfile
import unittest
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

    def test_archive_path_ascii_file(self):
        """Test the archive methods with an ASCII file path argument."""
        try:
            tempdir = tempfile.mkdtemp()
            out_dir = os.path.join(tempdir, 'extract')
            os.makedirs(out_dir)

            test_input = os.path.join(tempdir, 'testfile.txt')
            test_archive = os.path.join(tempdir, 'testfile.tar')
            test_output = os.path.join(out_dir, 'testfile.txt')

            # Create an archive from an ASCII file.
            _create_ascii_file(test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertFalse(os.path.exists(test_archive))
            self.assertEqual(self._FILE_TYPE_ASCII, _get_file_type(test_input))
            test_input_hash = _get_file_md5(test_input)
            backup.archive_path(test_archive, test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertTrue(os.path.isfile(test_archive))
            self.assertEqual(self._FILE_TYPE_ASCII, _get_file_type(test_input))
            self.assertEqual(test_input_hash, _get_file_md5(test_input))
            self.assertEqual(self._FILE_TYPE_TAR, _get_file_type(test_archive))
            test_archive_hash = _get_file_md5(test_archive)
            self.assertEqual(32, len(test_archive_hash))
            self.assertNotEqual(test_input_hash, test_archive_hash)

            # Un-archive the ASCII file.
            backup.unarchive_path(out_dir, test_archive)
            self.assertTrue(os.path.isfile(test_archive))
            self.assertTrue(os.path.isfile(test_output))
            self.assertEqual(self._FILE_TYPE_ASCII, _get_file_type(test_output))
            self.assertEqual(test_input_hash, _get_file_md5(test_output))
            self.assertEqual(self._FILE_TYPE_TAR, _get_file_type(test_archive))
            self.assertEqual(test_archive_hash, _get_file_md5(test_archive))

        finally:
            shutil.rmtree(tempdir)

    def test_archive_path_binary_file(self):
        """Test the archive methods with a binary file path argument."""
        try:
            tempdir = tempfile.mkdtemp()
            out_dir = os.path.join(tempdir, 'extract')
            os.makedirs(out_dir)

            test_input = os.path.join(tempdir, 'testfile.bin')
            test_archive = os.path.join(tempdir, 'binary_archive.tar')
            test_output = os.path.join(out_dir, 'testfile.bin')

            # Create an archive from a binary file.
            _create_binary_file(test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertFalse(os.path.exists(test_archive))
            self.assertEqual(self._FILE_TYPE_BINARY, _get_file_type(test_input))
            test_input_hash = _get_file_md5(test_input)
            backup.archive_path(test_archive, test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertTrue(os.path.isfile(test_archive))
            self.assertEqual(self._FILE_TYPE_BINARY, _get_file_type(test_input))
            self.assertEqual(test_input_hash, _get_file_md5(test_input))
            self.assertEqual(self._FILE_TYPE_TAR, _get_file_type(test_archive))
            test_archive_hash = _get_file_md5(test_archive)
            self.assertEqual(32, len(test_archive_hash))
            self.assertNotEqual(test_input_hash, test_archive_hash)

            # Un-archive the binary file.
            backup.unarchive_path(out_dir, test_archive)
            self.assertTrue(os.path.isfile(test_archive))
            self.assertTrue(os.path.isfile(test_output))
            self.assertEqual(self._FILE_TYPE_BINARY, _get_file_type(test_output))
            self.assertEqual(test_input_hash, _get_file_md5(test_output))
            self.assertEqual(self._FILE_TYPE_TAR, _get_file_type(test_archive))
            self.assertEqual(test_archive_hash, _get_file_md5(test_archive))

        finally:
            shutil.rmtree(tempdir)

    def test_archive_path_directory(self):
        """Test the archive methods with a directory path argument."""
        try:
            tempdir = tempfile.mkdtemp()
            out_dir = os.path.join(tempdir, 'extract')
            os.makedirs(out_dir)

            test_input = os.path.join(tempdir, 'struct')
            test_archive = os.path.join(tempdir, 'archive.tar')
            test_output = os.path.join(out_dir, 'struct')

            # Create an archive of the structure.
            _create_test_structure(test_input)
            self.assertTrue(os.path.isdir(test_input))
            self.assertFalse(os.path.exists(test_archive))
            self.assertEqual(self._FILE_TYPE_DIR, _get_file_type(test_input))
            test_input_hash = _get_dir_md5(test_input)
            backup.archive_path(test_archive, test_input)
            self.assertTrue(os.path.isdir(test_input))
            self.assertTrue(os.path.isfile(test_archive))
            self.assertEqual(self._FILE_TYPE_DIR, _get_file_type(test_input))
            self.assertEqual(test_input_hash, _get_dir_md5(test_input))
            self.assertEqual(self._FILE_TYPE_TAR, _get_file_type(test_archive))
            test_archive_hash = _get_file_md5(test_archive)
            self.assertEqual(32, len(test_archive_hash))

            # Un-archive the structure.
            backup.unarchive_path(out_dir, test_archive)
            self.assertTrue(os.path.isfile(test_archive))
            self.assertTrue(os.path.isdir(test_input))
            self.assertTrue(os.path.isdir(test_output))
            self.assertEqual(self._FILE_TYPE_DIR, _get_file_type(test_output))
            self.assertEqual(test_input_hash, _get_dir_md5(test_output))
            self.assertEqual(self._FILE_TYPE_TAR, _get_file_type(test_archive))
            self.assertEqual(test_archive_hash, _get_file_md5(test_archive))

        finally:
            shutil.rmtree(tempdir)

    def test_compress_path_ascii_file(self):
        """Test the compress methods with an ASCII file path argument."""
        try:
            tempdir = tempfile.mkdtemp()
            out_dir = os.path.join(tempdir, 'extract')
            os.makedirs(out_dir)

            test_input = os.path.join(tempdir, 'testfile.txt')
            test_compressed = os.path.join(tempdir, 'testfile.xz')
            test_output = os.path.join(out_dir, 'testfile.txt')

            # Compress an ASCII file.
            _create_ascii_file(test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertFalse(os.path.exists(test_compressed))
            self.assertEqual(self._FILE_TYPE_ASCII, _get_file_type(test_input))
            test_input_hash = _get_file_md5(test_input)
            backup.compress_path(test_compressed, test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertTrue(os.path.isfile(test_compressed))
            self.assertEqual(self._FILE_TYPE_ASCII, _get_file_type(test_input))
            self.assertEqual(test_input_hash, _get_file_md5(test_input))
            self.assertEqual(self._FILE_TYPE_XZ, _get_file_type(test_compressed))
            test_compressed_hash = _get_file_md5(test_compressed)
            self.assertEqual(32, len(test_compressed_hash))
            self.assertNotEqual(test_input_hash, test_compressed_hash)

            # Delete the ASCII file (so we can check it doesn't get recreated).
            os.remove(test_input)
            self.assertFalse(os.path.exists(test_input))

            # Decompress the ASCII file.
            backup.uncompress_path(test_output, test_compressed)
            self.assertFalse(os.path.exists(test_input))
            self.assertTrue(os.path.isfile(test_compressed))
            self.assertTrue(os.path.isfile(test_output))
            self.assertEqual(self._FILE_TYPE_ASCII, _get_file_type(test_output))
            self.assertEqual(test_input_hash, _get_file_md5(test_output))
            self.assertEqual(self._FILE_TYPE_XZ, _get_file_type(test_compressed))
            self.assertEqual(test_compressed_hash, _get_file_md5(test_compressed))

        finally:
            shutil.rmtree(tempdir)

    def test_compress_path_binary_file(self):
        """Test the compress methods with a binary file path argument."""
        try:
            tempdir = tempfile.mkdtemp()
            out_dir = os.path.join(tempdir, 'extract')
            os.makedirs(out_dir)

            test_input = os.path.join(tempdir, 'testfile.bin')
            test_compressed = os.path.join(tempdir, 'compressed.xz')
            test_output = os.path.join(out_dir, 'testfile.bin')

            # Compress a binary file.
            _create_binary_file(test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertFalse(os.path.exists(test_compressed))
            self.assertEqual(self._FILE_TYPE_BINARY, _get_file_type(test_input))
            test_input_hash = _get_file_md5(test_input)
            backup.compress_path(test_compressed, test_input)
            self.assertTrue(os.path.isfile(test_input))
            self.assertTrue(os.path.isfile(test_compressed))
            self.assertEqual(self._FILE_TYPE_BINARY, _get_file_type(test_input))
            self.assertEqual(test_input_hash, _get_file_md5(test_input))
            self.assertEqual(self._FILE_TYPE_XZ, _get_file_type(test_compressed))
            test_compressed_hash = _get_file_md5(test_compressed)
            self.assertEqual(32, len(test_compressed_hash))
            self.assertNotEqual(test_input_hash, test_compressed_hash)

            # Delete the binary file (so we can check it doesn't get recreated).
            os.remove(test_input)
            self.assertFalse(os.path.exists(test_input))

            # Decompress the binary file.
            backup.uncompress_path(test_output, test_compressed)
            self.assertFalse(os.path.exists(test_input))
            self.assertTrue(os.path.isfile(test_compressed))
            self.assertTrue(os.path.isfile(test_output))
            self.assertEqual(self._FILE_TYPE_BINARY, _get_file_type(test_output))
            self.assertEqual(test_input_hash, _get_file_md5(test_output))
            self.assertEqual(self._FILE_TYPE_XZ, _get_file_type(test_compressed))
            self.assertEqual(test_compressed_hash, _get_file_md5(test_compressed))

        finally:
            shutil.rmtree(tempdir)

if __name__ == '__main__':
    unittest.main()
