"""Test the logfetcher CLI."""

import runpy
import unittest
from unittest import mock

import logfetcher.__main__
import pyfakefs.fake_filesystem_unittest


class TestCli(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self) -> None:
        self.setUpPyfakefs()
        self.fs.create_dir('/path/to/directory')

    @mock.patch(
        'sys.argv', ['logfetcher', '--target', '/path/to/directory/some.log'])
    def test_main_entry_point_success(self) -> None:
        """Tests the main entry point with a valid path."""
        # This should run without raising an exception.
        runpy.run_module('logfetcher', run_name='__main__')

    @mock.patch(
        'sys.argv', ['logfetcher', '--target', '/non/existent/path/some.log'])
    def test_main_entry_point_not_found(self) -> None:
        """Tests the main entry point with a path that does not exist."""
        with self.assertRaises(FileNotFoundError):
            runpy.run_module('logfetcher', run_name='__main__')

    @mock.patch('logfetcher.__main__.main')
    def test_main_as_import(self, mock_main: mock.Mock) -> None:
        """Tests that main() is not called when imported as a module."""
        # This test is almost purely symbolic :-) just to reach 100% coverage.
        # We need to reload the module to ensure the top-level code is re-run,
        # as Python caches imports.
        import importlib
        importlib.reload(logfetcher.__main__)
        mock_main.assert_not_called()


if __name__ == "__main__":
    unittest.main()
