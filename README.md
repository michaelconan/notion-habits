# notion-habits

Simple Python application to create daily and weekly habit tracker records in Notion databases, executed via GitHub Actions

## Background

I use Notion as a habit tracker, among other things. Habits are tracked daily and weekly - a new row (page) needs to be added to the databases each day / week to record the habits.

Notion does not appear to have functionality to add these pages automatically, so I have used a few techniques to handle this:

- Zapier: I wanted to give this a try as I have worked with many other low-code integration tools. Unfortunately, the free version does not allow multiple-step zaps, which would be required for my use case.
- Google Apps Script: I use Apps Script for many personal automations, and got something up and running quickly for this case.
- Python: I primarily use Python in my professional work and saw this as an opportunity to try out GitHub actions as a script orchestration tool.

## Usage

The application has been developed to create daily and weekly Notion habit records, which can be executed as follows:

```sh
# Add daily habit record
pipenv run python ./run.py --type daily

# Add weekly habit record
pipenv run python ./run.py --type weekly
```

## Dependencies

Packages are managed using [Pipenv](https://pipenv.pypa.io/), which additionally [loads variables from an environment file](https://pipenv.pypa.io/en/latest/configuration.html#configuration-with-environment-variables) for development purposes.

I considered using [notion-py](https://pypi.org/project/notion/) but do not like the use of the browser cookie token rather than creating a [Notion integration](https://www.notion.so/profile/integrations) and using the internal secret / API key.