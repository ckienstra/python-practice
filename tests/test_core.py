"""Test the logfetcher."""

import logging
import os
import pathlib
import unittest
from unittest import mock

import logfetcher.core as core
import pyfakefs.fake_filesystem_unittest


class TestValidPath(pyfakefs.fake_filesystem_unittest.TestCase):

    def setUp(self) -> None:
        # Because pyfakefs needs to be setup before mocks, these tests don't
        # respond well to the @mock.patch decorator. Patch with a context
        # manager instead.
        self.setUpPyfakefs()
        self.fs.create_dir('/good/path')
        self.fs.cwd = '/good/path'
        self.mock_logger = mock.Mock(spec=logging.Logger)
        self.log_fetcher = core.LogFetcher(logger=self.mock_logger)

    def test_valid_path_success(self) -> None:
        """Test with a file in the current directory."""
        path = "."
        result = self.log_fetcher.valid_path(path)
        self.assertIsInstance(result, pathlib.Path)
        self.assertEqual(result, pathlib.Path('/good/path'))

    def test_valid_path_permission_error(self) -> None:
        """Test a path where permissions are denied."""
        self.fs.create_dir('/root', perm_bits=0o000)
        path = "/root/test.log"
        with self.assertRaises(core.PossibleSudoRequired):
            self.log_fetcher.valid_path(path)

    def test_valid_path_permission_error_on_access(self) -> None:
        """Test a path where the directory is not readable."""
        path = "/unreadable/path"
        # Create the directory so resolve(strict=True) passes.
        self.fs.create_dir(path)
        with mock.patch('logfetcher.core.os.access',
                        return_value=False) as mock_access:
            with self.assertRaises(core.PossibleSudoRequired):
                self.log_fetcher.valid_path(path)
            mock_access.assert_called_once_with(
                pathlib.Path(path).resolve(), os.R_OK)

    def test_valid_path_not_found(self) -> None:
        """Test a path that does not exist."""
        path = "/non/existent/path/file.log"
        with self.assertRaises(FileNotFoundError):
            self.log_fetcher.valid_path(path)


class TestMatchFiles(pyfakefs.fake_filesystem_unittest.TestCase):

    def setUp(self) -> None:
        self.setUpPyfakefs()
        self.fs.create_dir('/good/path')
        self.mock_logger = mock.Mock(spec=logging.Logger)
        self.log_fetcher = core.LogFetcher(logger=self.mock_logger)

    def test_match_files_success(self) -> None:
        """Test matching files with a glob pattern."""
        self.fs.create_file('/good/path/test1.log')
        self.fs.create_file('/good/path/test2.log')
        self.fs.create_file('/good/path/other.txt')
        dirpath = pathlib.Path('/good/path')
        matches = self.log_fetcher.match_files(dirpath, '*.log')
        self.assertEqual(len(matches), 2)
        self.assertIn(pathlib.Path('/good/path/test1.log'), matches)
        self.assertIn(pathlib.Path('/good/path/test2.log'), matches)

    def test_match_files_with_unresolvable_link(self) -> None:
        """Test that unresolvable symlinks are skipped."""
        self.fs.create_file('/good/path/real.log')
        self.fs.create_symlink('/good/path/broken.log',
                               '/non/existent/target')
        dirpath = pathlib.Path('/good/path')
        matches = self.log_fetcher.match_files(dirpath, '*.log')
        self.assertEqual(matches, [pathlib.Path('/good/path/real.log')])


class TestScrubExcluded(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = mock.Mock(spec=logging.Logger)
        self.log_fetcher = core.LogFetcher(logger=self.mock_logger)

    def test_scrub_excluded_success(self) -> None:
        """Test that excluded files are removed from matches."""
        targets = [pathlib.Path('/good/path/test1.log'),
                   pathlib.Path('/good/path/test2.log')]
        excludes = ['/good/path/test1.log']
        result = self.log_fetcher.scrub_excluded(targets, excludes)
        self.assertEqual(result, [pathlib.Path('/good/path/test2.log')])

    def test_scrub_excluded_no_excludes(self) -> None:
        """Test that no excluded files are removed from matches."""
        targets = [pathlib.Path('/good/path/test1.log'),
                   pathlib.Path('/good/path/test2.log')]
        excludes: list[str] = []
        result = self.log_fetcher.scrub_excluded(targets, excludes)
        self.assertEqual(result, targets)


class TestGatherFiles(pyfakefs.fake_filesystem_unittest.TestCase):

    def setUp(self) -> None:
        self.setUpPyfakefs()
        self.fs.create_dir('/good/path')
        self.fs.create_file('/good/path/test1.log')
        self.fs.create_file('/good/path/test2.log')
        self.mock_logger = mock.Mock(spec=logging.Logger)
        self.log_fetcher = core.LogFetcher(logger=self.mock_logger)

    def test_gather_files_success(self) -> None:
        expected = [pathlib.Path('/good/path/test1.log'),
                    pathlib.Path('/good/path/test2.log')]
        result = self.log_fetcher.gather_files(
            targets=['/good/path/test1.log', '/good/path/test2.log'],
            excludes=[])
        self.assertEqual(result, expected)

    def test_gather_files_with_excludes(self) -> None:
        expected = [pathlib.Path('/good/path/test1.log')]
        result = self.log_fetcher.gather_files(
            targets=['/good/path/test1.log', '/good/path/test2.log'],
            excludes=['*test2.*'])
        self.assertEqual(result, expected)

    @mock.patch('logfetcher.core.LogFetcher.valid_path',
                return_value=pathlib.Path('/good/path'))
    def test_gather_files_calls_valid_path(
            self, mock_valid_path: mock.Mock) -> None:
        """Test that gather_files calls valid_path for each target's parent."""
        self.log_fetcher.gather_files(
            targets=['/good/path/*.log'],
            excludes=[])
        mock_valid_path.assert_called_once_with('/good/path')

    def test_gather_files_with_dir_excludes(self) -> None:
        """Test that gather files will exclude whole dirs from results."""
        expected: list[pathlib.Path] = []
        result = self.log_fetcher.gather_files(
            targets=['/good/path/*.log'], excludes=['/good/path/*'])
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
