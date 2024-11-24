"""
habits.py

Module to create Notion records for habit tracker databases.
"""

# Base imports
import os
from logging import getLogger, Logger
from datetime import date

# Local imports
from .notion import NotionClient, NotionRecord


logger: Logger = getLogger(__name__)
RECORD_TYPES: dict = {
    "daily": {
        "parent": "DAILY_DATABASE_ID",
        "title": "Daily Habits:",
    },
    "weekly": {
        "parent": "WEEKLY_DATABASE_ID",
        "title": "Week:",
    },
}
"""dict: Mapping of habit record configurations for page properties"""


def get_habit_page(page_type: str) -> NotionRecord:
    """Get a page on the relevant habit database

    Args:
        page_type (str): Daily or Weekly habit page

    Raises:
        EnvironmentError: Missing Notion API key in environment
        EnvironmentError: Missing summary page identifier in environment
    """
    # Load and confirm API key available
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        raise EnvironmentError("No Notion API key available")

    # Connect to Notion API
    client = NotionClient(api_key=api_key)

    # Validate period is defined in configuration
    if page_type not in RECORD_TYPES:
        raise LookupError(f"Unable to identify record for {page_type} habits")

    # Get and validate parent database ID from environment
    period_record = RECORD_TYPES[page_type]
    parent_db = os.getenv(period_record["parent"])
    if not parent_db:
        raise EnvironmentError(
            f"Unable to identify {page_type} database identifier in environment")
    logger.info(f"Adding habit record to parent database: {parent_db}")

    # Get record body and create page
    summary_page = os.getenv("SUMMARY_PAGE_ID")
    if not summary_page:
        raise EnvironmentError("No Notion summary page identifier available")

    # Connect to Notion database
    database = client.get_database(parent_db)
    # Create instance of Notion record and set date
    today = date.today()
    record = database.new_record(
        name=f"{period_record['title']} {today.strftime('%b %d, %Y')}")
    record.date = today
    record.habit_analytics = summary_page
    logger.info(f"Created {page_type} habit record for database")

    # Make weekly-specifc updates
    if page_type == "weekly":
        # For weekly habit tasks, get latest week to link
        results = database.query(
            params={
                "page_size": 1,
                "sorts": [
                    {
                        "property": "Date",
                        "direction": "descending",
                    }
                ]
            })
        record.prior_weekly_discipline = results[0]._id

    # Provide page to commit
    return record
