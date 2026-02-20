"""logfetcher finds IP addresses in logs and displays their frequency."""

import logging

from .core import Error, LogFetcher, PossibleSudoRequired

__all__ = ["Error", "LogFetcher", "PossibleSudoRequired"]

# Add a NullHandler to the package's root logger to avoid "No handler found"
# warnings if the library is used by an application that doesn't have logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())
