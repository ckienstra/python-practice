"""Test the logfetcher."""

import os
import pathlib
import unittest
from unittest import mock

import logfetcher.core as core
import pyfakefs.fake_filesystem_unittest


class TestValidPath(pyfakefs.fake_filesystem_unittest.TestCase):

    def setUp(self) -> None:
        self.setUpPyfakefs()
        self.fs.create_dir('/path/to/directory')
        self.fs.cwd = '/path/to/directory'
        self.log_fetcher = core.LogFetcher()

    def test_valid_path_success(self) -> None:
        """Test with a file in the current directory."""
        path = "."
        result = self.log_fetcher.valid_path(path)
        self.assertIsInstance(result, pathlib.Path)
        self.assertEqual(result, pathlib.Path('/path/to/directory'))

    def test_valid_path_not_dir(self) -> None:
        """Test a path whose parent is a file, not a directory."""
        self.fs.create_file('/path/to/file', contents="test")
        path = "/path/to/file/test.log"
        with self.assertRaises(NotADirectoryError):
            self.log_fetcher.valid_path(path)

    def test_valid_path_permission_error(self) -> None:
        """Test a path where permissions are denied."""
        self.fs.create_dir('/root', perm_bits=0o000)
        path = "/root/test.log"
        with self.assertRaises(core.PossibleSudoRequired):
            self.log_fetcher.valid_path(path)

    @mock.patch('logfetcher.core.os.access', return_value=False)
    def test_valid_path_permission_error_on_access(
            self, mock_access: mock.Mock) -> None:
        """Test a path where the directory is not readable."""
        # Use a path that is known to exist to isolate the os.access check.
        path = "/path/to/directory/test.log"
        with self.assertRaises(core.PossibleSudoRequired):
            self.log_fetcher.valid_path(path)

        # Verify that our mock was called as expected.
        mock_access.assert_called_once_with(
            pathlib.Path('/path/to/directory'), os.R_OK)

    def test_valid_path_not_found(self) -> None:
        """Test a path that does not exist."""
        path = "/non/existent/path/file.log"
        with self.assertRaises(FileNotFoundError):
            self.log_fetcher.valid_path(path)


if __name__ == "__main__":
    unittest.main()
