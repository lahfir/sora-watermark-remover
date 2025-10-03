"""
Main entry point for the watermark removal CLI tool.

This module serves as the executable entry point when the package is installed.
"""

from src.cli import remove_watermark


def cli():
    """
    Entry point function for the CLI application.

    This function is referenced in pyproject.toml as the console script entry point.
    """
    remove_watermark()


if __name__ == "__main__":
    cli()
