"""logfetcher finds IP addresses in logs and displays their frequency."""
import logging
import os
from pathlib import Path


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
                f"Access denied during path resolution for \"{path}\", "
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
                self.logger.info("Unable to resolve file, skipping: "
                                 f"\"{file.absolute()}\", error: {e}")
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
