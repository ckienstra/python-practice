"""Test the logfetcher."""

import unittest

import pyfakefs.fake_filesystem_unittest

import logfetcher


class TestValidPath(pyfakefs.fake_filesystem_unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log_fetcher = logfetcher.LogFetcher()

    def setUp(self):
        self.setUpPyfakefs()
        self.fs.add_real_directory('/path/to/directory')
        self.fs.add_real_file('/path/to/directory/file-that-exists.log')
        self.fs.add_real_file('/path/to/directory/file-that-exists-2.log')
        assert not self.fs.exists(
            '/path/to/directory/file-that-does-not-exist.log')
        # How do I ensure that the current working directory is
        # '/path/to/directory'?
        # That way, '.' will map to '/path/to/directory'.

    def test_valid_path_success(self):
        # Test with current directory which should always be accessible
        path = "."
        result = self.log_fetcher.valid_path(path)
        self.assertIsInstance(result, logfetcher.Path)

    def test_valid_path_permission_error(self):
        # Test a path that typically requires sudo/root access
        path = "/root/test.log"
        with self.assertRaises(logfetcher.PossibleSudoRequired):
            self.log_fetcher.valid_path(path)

    def test_valid_path_not_found(self):
        # Test a non-existent directory
        path = "/non/existent/path/file.log"
        with self.assertRaises(FileNotFoundError):
            self.log_fetcher.valid_path(path)


class TestMain(unittest.TestCase):
    # Use a flagsaver decorator for argparse
    def test_main(self):
        pass


if __name__ == "__main__":
    unittest.main()
