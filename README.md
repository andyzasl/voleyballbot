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

## Deployment to Vercel

1. Create a Vercel account
2. Install Vercel CLI
3. Create a new Vercel project
4. Add environment variables:
   - BOT_TOKEN
   - DATABASE_URL
   - ADMIN_USER_ID

5. Deploy the application using:
```bash
npm run deploy
```

6. Set up the Telegram webhook:
   - Get your Vercel deployment URL
   - Set the Telegram webhook using:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_VERCEL_URL>/api/telegram"
```

## Production Requirements

- Vercel CLI
- Node.js 16+
- Python 3.9+ (for local development)
