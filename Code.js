// Global variables
const SPROPS = PropertiesService.getScriptProperties();
const BASE_URL = "https://api.notion.com/v1";
const API_VERSION = "2022-06-28";

// Database and page IDs
const DAILY_DATABASE_ID = "10140b50-0f0d-43d2-905a-7ed714ef7f2c";
const WEEKLY_DATABASE_ID = "11e09eb8-3f76-80e7-8fac-e8d0bb538fb0";
const SUMMARY_PAGE_ID = "158ae6e0-341c-474a-9063-3f5e834ce74c";

/**
 * Daily function to add task records
 */
function addTaskPages() {
  // On Monday, add new weekly record
  if (new Date().getDay() === 1) {
    addWeeklyRecord();
  }
  // Add new record each day
  addDailyRecord();
}

/**
 * Add new daily record to database
 */
function addDailyRecord() {
  // Create daily habit record body
  const currentDate = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "MMM dd, yyyy");
  const body = getPageBody(DAILY_DATABASE_ID, `Daily Habits: ${currentDate}`);

  // Create new daily task page
  const newDailyPage = callNotion("/pages", body);
  console.log("Created page: " + newDailyPage.id);
}

/**
 * Add new weekly record to database
 */
function addWeeklyRecord() {
  // Create weekly habit record body
  const currentDate = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "MMM dd, yyyy");
  const body = getPageBody(WEEKLY_DATABASE_ID, `Week: ${currentDate}`);

  // Query for latest page in weekly database
  const queryBody = {
    page_size: 1,
    //filter: {},
    sorts: [
      {
        property: "Date",
        direction: "descending"
      },
    ],
  }
  const queryResult = callNotion(`/databases/${WEEKLY_DATABASE_ID}/query`, queryBody);
  // Add latest page as prior link
  body.properties["Prior Weekly Discipline"] = {
    relation: [
      {
        id: queryResult.results[0].id,
      },
    ],
  };

  // Create new weekly task page
  const newWeeklyPage = callNotion("/pages", body);
  console.log("Created page: " + newWeeklyPage.id);
}

/**
 * Search function to identify database or page identifier
 */
function searchPages() {

  // Prepare search body
  const searchTerm = "Weekly Disciplines";
  const query = {
    query: searchTerm,
    filter: {
        value: "database",
        property: "object"
    },
    sort:{
      direction: "ascending",
      timestamp: "last_edited_time"
    }
  }

  // Call search API
  const response = callNotion("/search", query);
  console.log(response);
}

/**
 * @param {string} databaseId - Identifier of database for page parent
 * @param {string} pageTitle - Text title to assign to page
 * @return {object} Page object for Notion request
 */
function getPageBody(databaseId, pageTitle) {
  return {
    parent: {
      database_id: databaseId,
    },
    properties: {
      Name: {
        title: [
          {
            text: {
              content: pageTitle,
            }
          }
        ]
      },
      Date: {
        date: {
          start: new Date().toISOString().slice(0,10),
        }
      },
      "Habit Analytics": {
        relation: [
          {
            id: SUMMARY_PAGE_ID,
          }
        ]
      }
    }
  }
}

/**
 * @param {string} endpoint - Relative URL for Notion API request
 * @param {object} body - Payload body to provide to Notion endpoint
 * @return {object} Parsed response from API call
 */
function callNotion(endpoint, body) {
  // Call endpoint to create page
  const response = UrlFetchApp.fetch(
    BASE_URL + endpoint,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${SPROPS.getProperty("API_KEY")}`,
        "Notion-Version": API_VERSION,
      },
      contentType: "application/json",
      payload: JSON.stringify(body),
      muteHttpExceptions: true,
    }
  )
  // Validate and return response
  if (response.getResponseCode().toString().startsWith("2")) {
    return JSON.parse(response.getContentText());
  } else {
    throw new Error(response.getResponseCode().toString() + " " + response.getContentText());
  }
}
