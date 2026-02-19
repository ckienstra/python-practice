"""logfetcher finds IP addresses in logs and displays their frequency."""
import os
from pathlib import Path


class Error(Exception):
    """Base class for exceptions in this module."""


class PossibleSudoRequired(Error):
    """Exception raised when sudo might be needed to access a path."""


class LogFetcher:

    def valid_path(self, path: str) -> Path:
        """Validates that a path's parent directory exists and is readable."""
        dirpath: Path = Path(path)
        try:
            # strict=True will raise FileNotFoundError if path doesn't exist.
            resolved_path: Path = dirpath.parent.resolve(strict=True)
        except PermissionError as e:
            raise PossibleSudoRequired(
                f"Access denied during path resolution for \"{path}\", "
                "try again with sudo"
            ) from e

        if not resolved_path.is_dir():
            raise NotADirectoryError(
                f"{resolved_path} is not a directory."
            )

        # Also check for read access, which resolve() does not guarantee.
        if not os.access(resolved_path, os.R_OK):
            raise PossibleSudoRequired(
                f"No read access to directory {resolved_path}, "
                "try again with sudo"
            )

        return resolved_path

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
