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

Update the config.json with your bot token and database settings.

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
