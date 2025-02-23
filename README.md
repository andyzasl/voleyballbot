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
3. Install requirements: `pip install -r requirements.txt`
4. Initialize the database: `python -c "from utils import init_db; init_db()"`
5. Start the bot: `python bot.py`

## Configuration

Update the config.json with your bot token and database settings.

## Requirements

Python 3.9+
python-telegram-bot 20.0+
sqlalchemy 2.0+
