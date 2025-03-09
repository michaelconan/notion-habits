# Base imports
import os

# PyPI imports
import pytest


@pytest.fixture
def api_key() -> str:
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        raise EnvironmentError("No Notion API key available")
    return api_key


@pytest.fixture
def page_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "parent": {
                "type": "object",
                "properties": {
                    "database_id": {
                        "type": "string"
                    }
                }
            },
            "properties": {
                "type": "object"
            }
        }
    }

@pytest.fixture(params=("daily", "weekly", "monthly"))
def page_type(request) -> str:
    return request.param