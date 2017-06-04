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
Main test runner for tiny-backup.

Maintained at https://github.com/jonsim/tiny-backup
"""
import os.path
import subprocess
import sys
import unittest

#
# Shared testing defines.
#

GPG_HOME = os.path.join(sys.path[0], 'gpg-test-homedir')



#
# Shared testing methods.
#

def create_ascii_file(path, kb_size=16):
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

def create_binary_file(path, kb_size=16):
    """Creates a binary file.

    Args:
        path:       string path for the file to be written to.
        kb_size:    int (approximate) size, in KB, of the file to create.
    """
    assert not os.path.exists(path)
    with open(path, 'wb') as out_file:
        out_file.write(bytearray(range(256) * 4 * kb_size))

def create_test_dir(path):
    """Creates a test directory and populates it full of files.

    Args:
        path:       string path for the directory to be created at.
    """
    assert not os.path.exists(path)
    os.makedirs(path)
    create_ascii_file(os.path.join(path, 'file.txt'), 8)
    create_ascii_file(os.path.join(path, 'file.log'), 24)
    create_binary_file(os.path.join(path, 'file.bin'), 16)

def create_test_structure(path):
    """Creates a test directory structure with files and directories.

    Args:
        path:       string path for the directory structure to be created at.
    """
    assert not os.path.exists(path)
    os.makedirs(path)
    create_test_dir(os.path.join(path, 'test_dir1'))
    create_test_dir(os.path.join(path, 'test_dir1', 'test_subdir'))
    create_test_dir(os.path.join(path, 'test_dir2'))
    create_ascii_file(os.path.join(path, 'root_file.txt'))
    create_binary_file(os.path.join(path, 'root_file.bin'))

def get_file_md5(path):
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

def get_dir_md5(path):
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

def get_file_type(path):
    """Determines the file type of a path as given by the 'file' command.

    Args:
        path:   string path of the file whose type will be determined.

    Returns:
        string file type.
    """
    return subprocess.check_output(['file', '--brief', path]).strip()



#
# Main test runner.
#

def main():
    """Run all test suites."""
    # Life is too short to try to make Python's uniquely terrible package system
    # accept this as a nice package import.
    from unittests import TestBackupMethods
    from systemtests import TestBackupSystem
    # Load the tests.
    runner = unittest.TextTestRunner(descriptions=False, verbosity=2)
    ut_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestBackupMethods)
    st_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestBackupSystem)
    # Run the unit tests.
    print 'Running unit tests...\n'
    ut_res = runner.run(ut_suite)
    if not ut_res.wasSuccessful():
        sys.exit(1)
    print '\n\nRunning system tests...\n'
    st_res = runner.run(st_suite)
    if not st_res.wasSuccessful():
        sys.exit(1)
    print '\n\nAll tests passed.'
    sys.exit(0)

# Entry point.
if __name__ == "__main__":
    main()
