# notion-habits

Simple Python application to create daily, weekly, and monthly habit tracker records in Notion databases, executed via GitHub Actions.

## How It Works

Each day, a GitHub Actions workflow runs at 03:00 UTC and creates new pages in your Notion habit databases:

- **Daily** — created every day
- **Weekly** — created on Mondays
- **Monthly** — created on the 1st of each month

Each record is linked to a summary page in a "Habit Analytics" database and stamped with the current date.

## Prerequisites

- A Notion workspace with the following databases: `Daily Disciplines`, `Weekly Disciplines`, `Monthly Disciplines`, and `Habit Analytics`
- A [Notion integration](https://www.notion.so/profile/integrations) with access to those databases
- Python 3.12 and [Pipenv](https://pipenv.pypa.io/)

## Setup

### 1. Configure your Notion integration

Create a Notion internal integration and copy the API key (format: `ntn_...`). Share each of the four databases with the integration from the Notion UI.

### 2. Set up environment variables

```sh
cp example.env .env
# Edit .env and set NOTION_API_KEY=ntn_YOURKEYHERE
```

Pipenv loads `.env` automatically during local development.

### 3. Install dependencies

```sh
pipenv install
```

### 4. Configure GitHub Actions (for automated scheduling)

Add `NOTION_API_KEY` as a secret in a GitHub Actions environment named `notion`. The workflow in `.github/workflows/add_habits.yml` will pick it up automatically.

## Usage

Run the script manually to add a habit record:

```sh
# Add daily habit record
pipenv run python run.py --type daily

# Add weekly habit record
pipenv run python run.py --type weekly

# Add monthly habit record
pipenv run python run.py --type monthly
```

## Development

```sh
# Install dev dependencies
pipenv install --dev

# Run tests (requires NOTION_API_KEY in environment)
pipenv run pytest tests/ --cov=src/
```

## Background

I use Notion as a habit tracker. A new row needs to be added to each habit database each day/week/month to record habits for that period — Notion has no built-in way to do this automatically.

I explored a few approaches before settling on Python + GitHub Actions:

- **Zapier**: The free tier doesn't allow multi-step zaps, which are required here.
- **Google Apps Script**: Works well; a legacy implementation lives in `gascript/` for reference.
- **Python + GitHub Actions**: Better structure, easier testing, and a good opportunity to try GitHub Actions as a scheduling tool.

Dependencies are managed with [Pipenv](https://pipenv.pypa.io/). The Notion API is called directly using `requests` with a proper [Notion integration](https://www.notion.so/profile/integrations) API key rather than a browser cookie token.
