"""Command-line interface for logfetcher."""
import argparse

from .core import LogFetcher


def main() -> None:
    """Parses arguments and runs the log fetcher."""
    parser = argparse.ArgumentParser(
        description="Finds IP addresses in logs and displays their frequency."
    )
    parser.add_argument(
        "--target", help="The target file location and pattern.", required=True
    )
    args = parser.parse_args()
    log_fetcher = LogFetcher()
    log_fetcher.valid_path(args.target)


if __name__ == "__main__":
    main()
