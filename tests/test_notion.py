# Base imports
import json
import logging

# PyPI imports
from jsonschema import validate

# Local imports
from src.notion import NotionClient, NotionRecord
from src.habits import get_habit_page, RECORD_TYPES


def test_query_data_source(api_key: str, page_type: str):

    # GIVEN
    # Get weekly database identifier from environment
    db_name = RECORD_TYPES[page_type]["parent"]
    page_size = 5
    client = NotionClient(api_key=api_key)
    data_source = client.get_data_source(data_source_name=db_name)

    # WHEN
    # Call the Notion data source query API
    results = data_source.query(params={
        "page_size": page_size,
    })
    logging.info(f"{len(results)} results returned")

    # THEN
    # Validate results and data types
    assert all(isinstance(result, NotionRecord) for result in results)
    assert len(results) == page_size


def test_habit_record(page_schema: dict, page_type: str):

    # GIVEN
    # Get configurations based on page type

    # WHEN
    # Get habit Notion record object
    record = get_habit_page(page_type)
    api_body = record._get_api_body()

    # THEN
    # Validate record against schema
    logging.info(json.dumps(api_body))
    validate(api_body, page_schema)
