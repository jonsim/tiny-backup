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
import backup
import os
import shutil
import subprocess
import tempfile
import unittest

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

    def test_archive_path_file(self):
        try:
            tempdir = tempfile.mkdtemp()
            extract_dir = os.path.join(tempdir, 'extract')
            os.makedirs(extract_dir)

            txt_file = os.path.join(tempdir, 'testfile.txt')
            txt_archive = os.path.join(tempdir, 'testfile.tar')
            txt_output = os.path.join(extract_dir, 'testfile.txt')
            bin_file = os.path.join(tempdir, 'testfile.bin')
            bin_archive = os.path.join(tempdir, 'binary_archive.tar')
            bin_output = os.path.join(extract_dir, 'testfile.bin')

            # First create an archive from an ASCII file.
            _create_ascii_file(txt_file)
            self.assertTrue(os.path.isfile(txt_file))
            self.assertFalse(os.path.exists(txt_archive))
            self.assertEqual('ASCII text', _get_file_type(txt_file))
            txt_file_hash = _get_file_md5(txt_file)
            backup.archive_path(txt_archive, txt_file)
            self.assertTrue(os.path.isfile(txt_file))
            self.assertTrue(os.path.isfile(txt_archive))
            self.assertEqual('ASCII text', _get_file_type(txt_file))
            self.assertEqual(txt_file_hash, _get_file_md5(txt_file))
            self.assertEqual('POSIX tar archive (GNU)', _get_file_type(txt_archive))
            txt_archive_hash = _get_file_md5(txt_archive)
            self.assertEqual(32, len(txt_archive_hash))
            self.assertNotEqual(txt_file_hash, txt_archive_hash)

            # Second create an archive from a binary file.
            _create_binary_file(bin_file)
            self.assertTrue(os.path.isfile(bin_file))
            self.assertFalse(os.path.exists(bin_archive))
            self.assertEqual('raw G3 data, byte-padded', _get_file_type(bin_file))
            bin_file_hash = _get_file_md5(bin_file)
            backup.archive_path(bin_archive, bin_file)
            self.assertTrue(os.path.isfile(bin_file))
            self.assertTrue(os.path.isfile(bin_archive))
            self.assertEqual('raw G3 data, byte-padded', _get_file_type(bin_file))
            self.assertEqual(bin_file_hash, _get_file_md5(bin_file))
            self.assertEqual('POSIX tar archive (GNU)', _get_file_type(bin_archive))
            bin_archive_hash = _get_file_md5(bin_archive)
            self.assertEqual(32, len(bin_archive_hash))
            self.assertNotEqual(bin_file_hash, bin_archive_hash)
            self.assertNotEqual(txt_archive_hash, bin_archive_hash)

            # Un-archive the ASCII file.
            backup.unarchive_path(extract_dir, txt_archive)
            self.assertTrue(os.path.isfile(txt_archive))
            self.assertTrue(os.path.isfile(txt_output))
            self.assertEqual('ASCII text', _get_file_type(txt_output))
            self.assertEqual(txt_file_hash, _get_file_md5(txt_output))
            self.assertEqual('POSIX tar archive (GNU)', _get_file_type(txt_archive))
            self.assertEqual(txt_archive_hash, _get_file_md5(txt_archive))

            # Un-archive the binary file.
            backup.unarchive_path(extract_dir, bin_archive)
            self.assertTrue(os.path.isfile(bin_archive))
            self.assertTrue(os.path.isfile(bin_output))
            self.assertEqual('raw G3 data, byte-padded', _get_file_type(bin_output))
            self.assertEqual(bin_file_hash, _get_file_md5(bin_output))
            self.assertEqual('POSIX tar archive (GNU)', _get_file_type(bin_archive))
            self.assertEqual(bin_archive_hash, _get_file_md5(bin_archive))

        finally:
            shutil.rmtree(tempdir)

    def test_archive_path_directory(self):
        try:
            tempdir = tempfile.mkdtemp()
            extract_dir = os.path.join(tempdir, 'extract')
            os.makedirs(extract_dir)

            struct = os.path.join(tempdir, 'struct')
            archive = os.path.join(tempdir, 'archive.tar')
            output = os.path.join(extract_dir, 'struct')

            # Create an archive of the structure.
            _create_test_structure(struct)
            self.assertTrue(os.path.isdir(struct))
            self.assertFalse(os.path.exists(archive))
            self.assertEqual('directory', _get_file_type(struct))
            struct_hash = _get_dir_md5(struct)
            backup.archive_path(archive, struct)
            self.assertTrue(os.path.isdir(struct))
            self.assertTrue(os.path.isfile(archive))
            self.assertEqual('directory', _get_file_type(struct))
            self.assertEqual(struct_hash, _get_dir_md5(struct))
            self.assertEqual('POSIX tar archive (GNU)', _get_file_type(archive))
            archive_hash = _get_file_md5(archive)
            self.assertEqual(32, len(archive_hash))

            # Un-archive the structure.
            backup.unarchive_path(extract_dir, archive)
            self.assertTrue(os.path.isfile(archive))
            self.assertTrue(os.path.isdir(struct))
            self.assertTrue(os.path.isdir(output))
            self.assertEqual('directory', _get_file_type(output))
            self.assertEqual(struct_hash, _get_dir_md5(output))
            self.assertEqual('POSIX tar archive (GNU)', _get_file_type(archive))
            self.assertEqual(archive_hash, _get_file_md5(archive))

        finally:
            shutil.rmtree(tempdir)

if __name__ == '__main__':
    unittest.main()
