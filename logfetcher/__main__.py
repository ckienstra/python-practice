"""Command-line interface for logfetcher."""
import argparse
import logging
from pathlib import Path

from .core import LogFetcher


def main() -> None:
    """Parses arguments and runs the log fetcher."""
    parser = argparse.ArgumentParser(
        description="Finds IP addresses in logs and displays their frequency."
    )
    parser.add_argument(
        "--targets", help="The target file location and pattern.",
        required=True, nargs='+', type=str
    )
    parser.add_argument(
        "--excludes", help="File paths or patterns to exclude from search.",
        required=False, nargs='*', type=str, default="",
    )
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    log_fetcher = LogFetcher(logger)
    files: list[Path] = log_fetcher.gather_files(args.targets, args.excludes)

    logging.info(f"Matched files: {files}")


if __name__ == "__main__":
    main()
