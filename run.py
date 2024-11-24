# Base imports
import argparse
import logging

# Local imports
from src import habits

# Set INFO logging for terminal
logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Get command line arguments for script

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    # Create argument parser for command line options
    parser = argparse.ArgumentParser(
        description="Utility to add habit record pages to Notion databases.")
    parser.add_argument(
        "--type", type=str, help="Type of habit record to add to Notion", required=True)
    return parser.parse_args()


def main():
    """Entry point to execute script"""
    # Get record type argument
    args = parse_args()
    # Get habit page based on type provided
    page_type = args.type
    record = habits.get_habit_page(page_type)
    record.commit()
    logger.info(f"Created {page_type} habit record: {record.id}")


if __name__ == "__main__":
    main()
