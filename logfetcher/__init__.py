"""logfetcher finds IP addresses in logs and displays their frequency."""

from .core import Error, LogFetcher, PossibleSudoRequired

__all__ = ["Error", "LogFetcher", "PossibleSudoRequired"]
