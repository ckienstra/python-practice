"""Test the logfetcher."""

import unittest

import pyfakefs.fake_filesystem_unittest

import logfetcher.core as core


class TestValidPath(pyfakefs.fake_filesystem_unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log_fetcher = core.LogFetcher()

    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_dir('/path/to/directory')
        self.fs.cwd = '/path/to/directory'

    def test_valid_path_success(self):
        """Test with a file in the current directory."""
        path = "."
        result = self.log_fetcher.valid_path(path)
        self.assertIsInstance(result, core.Path)
        self.assertEqual(result, core.Path('/path/to/directory'))

    def test_valid_path_not_dir(self):
        """Test a path whose parent is a file, not a directory."""
        self.fs.create_file('/path/to/file', contents="test")
        path = "/path/to/file/test.log"
        with self.assertRaises(NotADirectoryError):
            self.log_fetcher.valid_path(path)

    def test_valid_path_permission_error(self):
        """Test a path where permissions are denied."""
        self.fs.create_dir('/root', perm_bits=0o000)
        path = "/root/test.log"
        with self.assertRaises(core.PossibleSudoRequired):
            self.log_fetcher.valid_path(path)

    def test_valid_path_permission_error_on_access(self):
        """Test a path where the directory is not readable."""
        # Create a directory with execute but not read permissions
        self.fs.create_dir('/no_read_dir', perm_bits=0o100)
        path = "/no_read_dir/test.log"
        with self.assertRaises(core.PossibleSudoRequired):
            self.log_fetcher.valid_path(path)

    def test_valid_path_not_found(self):
        """Test a path that does not exist."""
        path = "/non/existent/path/file.log"
        with self.assertRaises(FileNotFoundError):
            self.log_fetcher.valid_path(path)


if __name__ == "__main__":
    unittest.main()
