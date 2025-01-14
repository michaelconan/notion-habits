"""
notion.py

Custom Python client for Notion API to query databases, add records
and manage field interactions.
"""

# Base imports
import re
from logging import getLogger, Logger
from datetime import date, datetime
import enum
from typing import Any

# PyPI imports
import requests

logger: Logger = getLogger(__name__)


def get_slug(value: str) -> str:
    """Convert string to snake case property slug

    Args:
        value (str): Field name to convert to slug

    Returns:
        str: Slugified field name for property
    """
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '_', value)
    return value


class NotionException(Exception):
    """Custom Notion exception class"""
    pass


class NotionClient:
    """Notion API interface for integrations"""

    BASE_URL = "https://api.notion.com/v1"
    """str: Base link for API endpoints"""
    API_VERSION = "2022-06-28"
    """str: API version to use in requests"""
    METADATA_FIELDS = ["id", "url", "created_time", "last_edited_time"]
    """list[str]: Metadata fields related to all Notion objects"""

    def __init__(self, api_key: str):
        """Constructor for Notion client

        Args:
            api_key (str): Internal secret API key from Notion integration 
        """
        self.__api_key = api_key

    def request(self, endpoint: str, method: str, payload: dict = None) -> dict:
        """Make request to Notion API

        Args:
            endpoint (str): Relative URL of Notion API endpoint
            method (str): Method of HTTP request
            payload (dict, optional): Body to provide in API request. Defaults to None.

        Raises:
            requests.RequestException: Unsuccessful HTTP request

        Returns:
            dict: Parsed API response
        """
        # Call Notion API with arguments and headers
        response = requests.api.request(
            url=self.BASE_URL + endpoint,
            method=method,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.__api_key}",
                "Notion-Version": self.API_VERSION,
            }
        )
        # Validate and parse response or raise exception
        if response.ok:
            return response.json()
        else:
            raise requests.RequestException(response.text, response=response)

    def get_database(self, database_id: str = None, database_name: str = None) -> "NotionDatabase":
        """Get Notion database object using client integration

        Args:
            database_id (str): Identifier for Notion database
            database_name (str): Name of Notion database

        Returns:
            NotionDatabase: Database object from Notion page
        
        Raises:
            NotionException: No database found with provided identifier or name
        """
        # Get database using client and identifier
        if database_id:
            return NotionDatabase(client=self, id=database_id)
        elif database_name:
            result = self.request("/search", "POST", {
                "query": database_name,
                "filter": {"property": "object", "value": "database"},
            })
            matched_results = [
                d for d
                in result["results"]
                if "".join(t["plain_text"] for t in d["title"]) == database_name
            ]
            if matched_results:
                return NotionDatabase(client=self, id=matched_results[0]["id"])
        raise NotionException("No database found with provided identifier or name")

class NotionDatabase:
    """Structured set of Notion pages with defined properties"""

    def __init__(self, client: NotionClient, id: str):
        """Constructor for Notion database

        Args:
            client (NotionClient): Initialized client with credentials
            id (str): Identifier for database
        """
        # Set basic attributes
        self._id = id
        self.client = client

        # Load properties from API
        self._load_properties()

    def _load_properties(self):
        """Retrieve and store properties defined for database"""
        # Get details of database from API
        details = self.client.request(
            endpoint=f"/databases/{self.id}", method="GET")

        # Set metadata fields as object properties
        for field in self.client.METADATA_FIELDS:
            setattr(self, "_" + field, details[field])

        # Parse text-based attributes
        self.title = FieldType.TITLE.parse(details["title"])
        self.description = FieldType.RICH_TEXT.parse(details["description"])

        # Assign properties to attribute
        self._properties = details["properties"]

    @property
    def id(self) -> str:
        """Getting method for ID

        Note:
            No setter method to prevent override

        Returns:
            str: Identifier for database
        """
        return self._id

    @property
    def properties(self) -> dict[str, str]:
        """Slugified database properties (schema)

        Returns:
            dict[str, str]: Database properties
        """
        return {get_slug(k): v for k, v in self._properties.items()}

    def query(self, params: dict) -> list["NotionRecord"]:
        """Query a Notion database with parameters

        Args:
            params (dict): Parameters for database query

        Notes:
            Define filters for the query request using 
            `Notion structure.<https://developers.notion.com/reference/post-database-query>`_

        Returns:
            list[NotionRecord]: Records returned from database query
        """
        # Query a Notion database using query parameters
        results = self.client.request(
            f"/databases/{self.id}/query", "POST", params)
        # Parse results to record objects
        return [
            NotionRecord.from_api(parent=self, payload=result)
            for result in results["results"]
        ]

    def new_record(self, name: str) -> "NotionRecord":
        """Create a new record for the database

        Args:
            name (str): Value for title field of database

        Returns:
            NotionRecord: Record instance for database row
        """
        # Get record with name and parent database reference
        return NotionRecord(name=name, parent=self)


class NotionRecord:
    """Representation of a row page in a database collection"""

    def __init__(self, name: str, parent: "NotionDatabase"):
        """Constructor for new Database Record (row)

        Args:
            name (str): Value for title field of database
            parent (NotionDatabase): Parent database for record.
        """
        # Set initial properties
        self._id = None
        self._parent = parent
        # Set name as Notion Field object
        self.name = NotionField(record=self, name="name",
                                value=name, field_type="title")

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, self.name.value)

    @classmethod
    def from_api(cls, parent: NotionDatabase, payload: dict) -> "NotionRecord":
        """Create instance from API response

        Args:
            parent (NotionDatabase): Database to which record belongs
            payload (dict): Payload retrieved from Notion API

        Returns:
            NotionRecord: Record created from API response
        """
        # Get title property (often 'Name')
        title_property = [
            v for v in payload["properties"].values() if v["type"] == "title"][0]
        title_value = FieldType.TITLE.parse(title_property["title"])

        # Create record instance
        record = cls(name=title_value, parent=parent)

        # Create class instance and add metadata attributes
        logger.info(f"Parsing Notion page record: {
                    payload['id']}, {title_value}")
        for field in parent.client.METADATA_FIELDS:
            value = payload[field]
            if field.endswith("_time"):
                value = datetime.fromisoformat(payload[field])
            setattr(record, "_" + field, value)

        # Parse properties from query result payload
        properties = dict()
        for property, details in payload["properties"].items():
            field = NotionField.from_api(
                record=record, name=property, details=details)
            properties[field.name] = field

        # Assign record field properties
        for property, value in properties.items():
            if property != "name":
                setattr(record, property, value)

        return record

    @property
    def id(self) -> str:
        """Getter method for ID property

        Note:
            No setter is specified to avoid override

        Returns:
            str: Record identifier
        """
        return self._id

    @property
    def fields(self) -> dict:
        """Public record fields as dictionary

        Returns:
            dict: Fields and values for record
        """
        return {
            var: val for var, val in vars(self).items() if var[0] != "_"
        }

    def asdict(self) -> dict:
        """Public fields with values returned directly

        Returns:
            dict: Fields with parsed values
        """
        # Get values from fields
        fields = dict()
        for var, val in self.fields.items():
            if isinstance(val, NotionField):
                val = val.value
            fields[var] = val
        return fields

    @property
    def values(self) -> list[Any]:
        """List of field values

        Returns:
            list[Any]: Values from Notion fields
        """
        return [val for _, val in self.fields]

    def _get_api_body(self) -> dict:
        """Structure record data for API requests

        Returns:
            dict: Representation of Notion Record for API requests
        """
        properties = dict()

        # Check for record properties not on database
        invalid_properties = [
            k for k in self.fields.keys() if k not in self._parent.properties]
        if invalid_properties:
            raise NotionException(f"Record properties do not exist on parent database: {
                                  ', '.join(invalid_properties)}")

        # Format all NotionField properties for API requests
        for var, val in self.fields.items():
            if not isinstance(val, NotionField):
                val = NotionField(record=self, name=var, value=val)
            # Add API-formatted field to body dictionary
            properties = {**properties, **val.get_api_format()}

        body = {
            "properties": properties,
            "parent": {},
        }
        if self._parent:
            body["parent"]["database_id"] = self._parent.id

        return body

    def commit(self) -> str:
        """Update record values in Notion

        Returns:
            str: Identifier from committed record
        """
        # If ID is set (record exists), update
        if self._id:
            result = self._parent.client.request(
                f"/pages/{self._id}", "PATCH", self._get_api_body())
        else:
            # Create new page and retrieve ID
            result = self._parent.client.request(
                "/pages", "POST", self._get_api_body())
            self._id = result["id"]

        return self._id


class NotionField:
    """Field in Notion with name, type and value"""

    def __init__(self, record: NotionRecord, name: str, value: Any, field_type: str = None):
        """Constructor for NotionField object

        Args:
            record (NotionRecord): Record to which field belongs
            name (str): Name of field in the Notion collection
            value (Any): Value of Notion field
            field_type (str, optional): Type of Notion field, detected if not specified.
        """
        # Assign basic attributes
        self._record = record
        self.name = name
        # Detect field type if not specified
        if field_type:
            self.type = FieldType(field_type)
        else:
            self.type = FieldType.detect(value)
        self.value = value

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, self.display_name)

    @classmethod
    def from_api(cls, record: NotionRecord, name: str, details: dict) -> "NotionField":
        """Create NotionField instance from API response

        Args:
            record (NotionRecord): Record to which field belongs
            name (str): Name of Notion Field
            details (dict): Details from API response

        Returns:
            NotionField: Instance of Notion Field
        """
        # Convert name to snake case
        name = get_slug(name)
        # Get field type to parse value
        field_type = FieldType(details["type"])
        if details[field_type.value]:
            field_value = field_type.parse(details[field_type.value])
        else:
            field_value = None
        # Return class instance
        return cls(record=record, name=name, value=field_value, field_type=field_type)

    def get_api_format(self) -> dict:
        """Return API format dictionary for request

        Returns:
            dict: Mapping of display name and API body
        """
        return {
            self.display_name: self._api_body,
        }

    @property
    def display_name(self) -> str:
        """Display name of field within interface

        Returns:
            str: Formatted field name
        """
        return self._record._parent.properties[self.name]["name"]

    @property
    def _api_body(self) -> dict:
        """Generate API body structure for requests

        Returns:
            dict: API structure for field based on type
        """
        if self.type == FieldType.TITLE:
            return {
                "title": [
                    {
                        "text": {
                            "content": self.value,
                        }
                    }
                ]
            }
        elif self.type == FieldType.RICH_TEXT:
            return {
                "rich_text": [
                    {
                        "text": {
                            "content": self.value,
                        }
                    }
                ]
            }
        elif self.type == FieldType.DATE:
            return {
                "date": {
                    "start": self.value.isoformat(),
                }
            }
        elif self.type == FieldType.RELATION:
            return {
                "relation": [{
                    "id": self.value,
                }]
            }
        else:
            # fallback to type: value
            return {
                self.type: self.value,
            }


class FieldType(enum.Enum):
    """Notion field types and conversion methods"""

    CHECKBOX = "checkbox"
    CREATED_BY = "created_by"
    CREATED_TIME = "created_time"
    DATE = "date"
    EMAIL = "email"
    ICON = "icon"
    FILES = "files"
    FORMULA = "formula"
    LAST_EDITED_BY = "last_edited_by"
    LAST_EDITED_TIME = "last_edited_time"
    MULTI_SELECT = "multi_select"
    NUMBER = "number"
    PHOME_NUMBER = "phone_number"
    RELATION = "relation"
    RICH_TEXT = "rich_text"
    ROLLUP = "rollup"
    SELECT = "select"
    TITLE = "title"
    URL = "url"

    @classmethod
    def detect(cls, value: Any) -> "FieldType":
        """Determine type of Notion field by value

        Args:
            value (Any): Value of field to detect from

        Returns:
            FieldType: Enum instance value matching value
        """
        # Format of Notion identifier for relation fields
        GUID_FORMAT = r"\w{8}\-\w{4}\-\w{4}\-\w{4}\-\w{12}"
        # Return enum value based on variable type
        if isinstance(value, (date, datetime)):
            return cls.DATE
        elif isinstance(value, str):
            # Detect GUID format used for links
            if re.match(GUID_FORMAT, value):
                return cls.RELATION
            else:
                return cls.RICH_TEXT
        elif isinstance(value, bool):
            return cls.CHECKBOX
        elif isinstance(value, list):
            return cls.MULTI_SELECT
        elif isinstance(value, (int, float)):
            return cls.NUMBER

    def parse(self, details: dict | bool) -> Any:
        """Parse Notion API payload based on field type

        Args:
            details (dict | bool): Field details returned from API

        Returns:
            Any: Value of parsed field with type converted
        """
        # Parse values based on field type
        if self.value == "date":
            return date.fromisoformat(details["start"])
        elif self.value == "created_by":
            return details["id"]
        elif self.value in ("title", "rich_text"):
            return "".join(t["plain_text"] for t in details)
        elif self.value == "relation":
            return [r["id"] for r in details]
        elif self.value in ("formula", "rollup"):
            return details[details["type"]]
        else:
            # Simple values or adapters not identified
            return details
