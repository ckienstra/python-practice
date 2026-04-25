"""logfetcher finds IP addresses in logs and displays their frequency."""

from collections import Counter
import concurrent.futures
import logging
import os
from pathlib import Path
import typing

# Google RE2 offers some speed benefits versus default re
try:
    import re2 as re  # type: ignore
except ImportError:
    import re


class Error(Exception):
    """Base class for exceptions in this module."""


class PossibleSudoRequired(Error):
    """Exception raised when sudo might be needed to access a path."""


class LogFetcher:
    """LogFetcher is an object to fetch logs and find IP addresses."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the LogFetcher."""
        # Use the provided logger or get a logger for the current module.
        self.logger = logger or logging.getLogger(__name__)

    def valid_path(self, path: str) -> Path:
        """Validates that a path's parent directory exists and is readable."""
        dirpath: Path = Path(path)
        try:
            # strict=True will raise FileNotFoundError if path doesn't exist.
            resolved_path: Path = dirpath.resolve(strict=True)
        except PermissionError as e:
            raise PossibleSudoRequired(
                f'Access denied during path resolution for "{path}", '
                "try again with sudo"
            ) from e

        # Also check for read access, which resolve() does not guarantee.
        if not os.access(resolved_path, os.R_OK):
            raise PossibleSudoRequired(
                f"No read access to directory {resolved_path}, "
                "try again with sudo"
            )

        return resolved_path

    def match_files(
        self,
        dirpath: Path,
        pattern: str,
    ) -> list[Path]:
        """Match files against a pattern."""
        matches: list[Path] = []
        for file in dirpath.glob(pattern):
            try:
                matches.append(file.resolve(strict=True))
            except OSError as e:
                self.logger.info(
                    "Unable to resolve file, skipping: "
                    f'"{file.absolute()}", error: {e}'
                )
        return matches

    def scrub_excluded(
        self,
        matches: list[Path],
        excludes: list[str],
    ) -> list[Path]:
        """Remove excluded files from matches."""
        scrubbed_matches: list[Path] = matches.copy()
        # Exclude is almost certainly a smaller list than matches.
        for exclude in excludes:
            for file in matches:
                if file.match(exclude, case_sensitive=True):
                    scrubbed_matches.remove(file)
        return scrubbed_matches

    def gather_files(
        self,
        targets: list[str],
        excludes: list[str],
    ) -> list[Path]:
        """Gather files from a list of targets."""
        matches: list[Path] = []
        for target in targets:
            parent: str = target.rsplit("/", 1)[0]
            pattern: str = target.rsplit("/", 1)[1]
            resolved_dir: Path = self.valid_path(parent)
            files: list[Path] = self.match_files(resolved_dir, pattern)
            scrubbed_files: list[Path] = self.scrub_excluded(files, excludes)
            matches.extend(scrubbed_files)
        return matches


class LogScanner:
    """LogScanner is an object to scan logs for IP addresses."""

    def __init__(
        self,
        files: list[Path],
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the LogScanner.

        Args:
            files: The files to scan.
            logger: The logger to use.
        """
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        # Don't assign type hints for property overloads
        self.files = files
        # A Counter is like a dict[str, int] with convenience methods.
        self.ip_count: Counter[str] = Counter()
        self.ip_re: typing.Pattern[str] | typing.Any = re.compile(
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        )

    @property
    def files(self) -> list[Path]:
        """Get the files to scan."""
        return self._files

    @files.setter
    def files(self, files: list[Path]) -> None:
        """Input checking for files to scan."""
        if len(files) == 0:
            raise ValueError("files cannot be empty")
        self._files = files

    def scan_file(self, file: Path) -> Counter[str]:
        """Scan a file for IP addresses and return a counter of them."""
        ip_counter: Counter[str] = Counter()
        try:
            with open(file, encoding="utf-8") as f:
                for line in f:
                    # re2.search might be too memory intensive for large files.
                    # We can instead pass a per-line findall iterable directly.
                    ip_counter.update(self.ip_re.findall(line))
        except OSError as e:
            # The goal is to scan as much as possible, best-effort.
            self.logger.error(
                'Unable to read file "%s". Skipping: %s', file, e
            )
        return ip_counter

    def scan_files_serialized(self) -> None:
        """Scan files serially."""
        for file in self.files:
            self.ip_count.update(self.scan_file(file))

    def scan_files_parallel(self) -> None:
        """Scan files in parallel."""
        # Remember that thread pools are concurrent, not multiprocessed.
        # This feels ideal for filesystem I/O.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(self.scan_file, self.files)
            # Results are combined serially, so no lock is needed.
            for result_counter in results:
                self.ip_count.update(result_counter)

    def print_results(self) -> None:
        """Print the results."""
        for ip, count in self.ip_count.most_common():
            print(f"{ip}: {count}")


# Organizing my thoughts:
# What does this program do?
# It gets logs from a filesystem, finds IP addresses, and prints how many times
# each IP address is seen in each file.
# What does it not do?
# I am wondering if argument parsing is best left to a dedicated
# "logfetcher-cli.py" file.
# Whta steps will it take?
# 1. Accept user input for a file path supporting regex
# 2. Search the filesystem for files that match user input
# 3. Find IP addresses in each file and store them in a dict of
#    IP : occurrences
# 4. Display the final IP address count
#
# How should this program be organized into classes and methods?
# There should be helper methods for:
# 1. Check if base path if accessible, catching IOError, and asking if the
#    user has the right permissions to run the script on that file location.
#    Perhaps call it "path validator".
# 2. Matching files via regex. Use try/except in case some files aren't
#    accessible or are removed. Perhaps store the errors for the final print
#    statement. Matched files should be stored in a list.
#    NOTE: pathlib has a "match" method.
# 3. Have a dedicated method for scanning a file and producing a dict.
# 4. Have a different method that runs the file scanner method in a loop,
#    combines the dict results, and prints.
# -  Maybe the file scanner should accept a dict and modify it in-place.
# -  Later, mutex logic can be researched.
