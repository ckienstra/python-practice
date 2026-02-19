"""Test the logfetcher."""

import unittest
from unittest import mock

import pyfakefs.fake_filesystem_unittest

import logfetcher


class TestValidPath(pyfakefs.fake_filesystem_unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log_fetcher = logfetcher.LogFetcher()

    def setUp(self):
        self.setUpPyfakefs()
        assert not self.fs.exists(
            '/path/to/directory/file-that-does-not-exist.log')
        self.fs.create_dir('/path/to/directory')
        self.fs.create_file('/path/to/directory/file-that-exists.log')
        self.fs.create_file('/path/to/directory/file-that-exists-2.log')
        self.fs.cwd = '/path/to/directory'

    @mock.patch('os.getcwd', return_value='/path/to/directory')
    def test_valid_path_success(self, mock_getcwd):
        """Test with a file in the current directory."""
        path = "."
        result = self.log_fetcher.valid_path(path)
        self.assertIsInstance(result, logfetcher.Path)
        self.assertEqual(result, logfetcher.Path('/path/to/directory'))

    @mock.patch(
        'os.path.isdir', return_value=False, side_effect=PermissionError)
    def test_valid_path_permission_error(self, mock_isdir):
        """Test a path where permissions are denied."""
        self.fs.create_dir('/root', perm_bits=0o000)
        path = "/root/test.log"
        with self.assertRaises(logfetcher.PossibleSudoRequired):
            self.log_fetcher.valid_path(path)

    @mock.patch(
        'os.path.isdir', return_value=False, side_effect=FileNotFoundError)
    def test_valid_path_not_found(self, mock_isdir):
        """Test a path that does not exist."""
        path = "/non/existent/path/file.log"
        with self.assertRaises(FileNotFoundError):
            self.log_fetcher.valid_path(path)


class TestMain(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_dir('/path/to/directory')

    @mock.patch(
        'sys.argv',
        ['logfetcher.py', '--target', '/path/to/directory/some.log'])
    def test_main(self):
        """Tests that main runs without raising an exception."""
        logfetcher.main()


if __name__ == "__main__":
    unittest.main()
