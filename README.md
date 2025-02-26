# Volleyball Player Management Bot

A Python-based system to manage volleyball community players with Telegram integration.

## Features

- Player registration through Telegram
- Skill assessment survey system
- Event management
- Balanced team creation
- Player statistics tracking
- Telegram bot interface

## Setup

1. Clone the repository
2. Create a config.json from the template
3. Install the package in development mode:
```bash
pip install -e .
# or
uv install
```
4. Initialize the database:
```bash
python -m utils.init_db
```
5. Start the bot:
```bash
volleybot
# or
python -m bot
```

## Configuration

Configure the bot using environment variables.

## Deployment (Vercel)

1.  Create a Vercel account and project.
2.  Connect your GitHub repository to Vercel.
3.  Set the environment variables in the Vercel project settings.
4.  Ensure that the `vercel.json` file is present in the root directory.
5.  Deploy the project.

## Development

To set up a development environment:

1. Install the package with development dependencies:
```bash
pip install -e .[testing]
```

2. Run tests:
```bash
python -m pytest tests/
```

3. Run type checks (optional):
```bash
python -m mypy .
```

## Requirements

Python 3.9+
pip 22+
setuptools 42+
