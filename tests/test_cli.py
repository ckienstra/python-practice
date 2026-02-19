"""Test the logfetcher CLI."""

import runpy
import unittest
from unittest import mock

import pyfakefs.fake_filesystem_unittest


class TestCli(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_dir('/path/to/directory')

    @mock.patch(
        'sys.argv', ['logfetcher', '--target', '/path/to/directory/some.log'])
    def test_main_entry_point_success(self):
        """Tests the main entry point with a valid path."""
        # This should run without raising an exception.
        runpy.run_module('logfetcher', run_name='__main__')

    @mock.patch(
        'sys.argv', ['logfetcher', '--target', '/non/existent/path/some.log'])
    def test_main_entry_point_not_found(self):
        """Tests the main entry point with a path that does not exist."""
        with self.assertRaises(FileNotFoundError):
            runpy.run_module('logfetcher', run_name='__main__')


if __name__ == "__main__":
    unittest.main()
