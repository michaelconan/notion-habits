"""
habits.py

Module to create Notion records for habit tracker databases.
"""

# Base imports
import os
from logging import getLogger, Logger
from datetime import date

# Local imports
from src.notion import NotionClient, NotionRecord


logger: Logger = getLogger(__name__)
RECORD_TYPES: dict = {
    "daily": {
        "parent": "Daily Disciplines",
        "title": "Daily Habits:",
    },
    "weekly": {
        "parent": "Weekly Disciplines",
        "title": "Week:",
    },
    "monthly": {
        "parent": "Monthly Disciplines",
        "title": "Month:",
    },
}
"""dict: Mapping of habit record configurations for page properties"""

ANALYTICS_DB_NAME: str = "Discipline Analytics"
"""str: Name of the database for habit analytics"""


def get_habit_page(page_type: str) -> NotionRecord:
    """Get a page on the relevant habit database

    Args:
        page_type (str): Daily or Weekly habit page

    Raises:
        EnvironmentError: Missing Notion API key in environment
        LookupError: Unable to identify page type record for habits
        LookupError: Unable to identify summary page identifier from analytics database
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
    parent_db_name = period_record["parent"]
    logger.info(f"Adding habit record to parent database: {parent_db_name}")

    # Connect to Notion databases
    analytics_db = client.get_database(database_name=ANALYTICS_DB_NAME)
    summary_results = analytics_db.query(
        params={
            "filter": {
                "property": "Name",
                "title": {
                    "starts_with": parent_db_name.split(" ")[0]
                }
            }
        })
    if not summary_results:
        raise LookupError(f"No summary page found for {parent_db_name}")
    else:
        summary_page = summary_results[0].id
    database = client.get_database(database_name=parent_db_name)
    # Create instance of Notion record and set date
    today = date.today()
    record = database.new_record(
        name=f"{period_record['title']} {today.strftime('%b %d, %Y')}")
    record.date = today
    record.discipline_analytics = summary_page
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
        # Update record with prior week details
        record.prior_weekly_discipline = results[0].id
        record.days = results[0].days

    # Provide page to commit
    return record
