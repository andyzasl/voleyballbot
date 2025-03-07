import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import logging
import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from telegram import Update, Bot
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv
from utils.db import create_db_engine, create_db_session
import bot  # Import the bot module

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_IDS = [
    int(admin_id) for admin_id in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
]
MODE = os.environ.get("MODE", "webhook")  # Force webhook mode
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize Telegram bot application
bot_status = "Not Initialized"
application = None  # Define application outside the if block
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
    bot_status = "Error: TELEGRAM_BOT_TOKEN not found"
else:
    try:
        # Create a Bot instance
        telegram_bot = Bot(TELEGRAM_BOT_TOKEN)
        # Initialize the Application with the bot instance
        application = ApplicationBuilder().bot(telegram_bot).build()
        bot_status = "Initialized"
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        bot_status = f"Error: {e}"


# Database connection
db_status = "Not Connected"
try:
    config = {"database": {"dialect": "sqlite", "name": "volleybot.db"}}
    engine = create_db_engine(config=config)
    Session = create_db_session(engine)
    db_status = "Connected"
except Exception as e:
    logger.error(f"Failed to connect to the database: {e}")
    db_status = f"Error: {e}"

# Define a dependency to get a database session
def get_db_session():
    engine = create_db_engine(config=config)
    Session = create_db_session(engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

if application:
    # Register Telegram handlers
    application.add_handler(CommandHandler("start", lambda update, context: bot.start(update, context, engine, Session)))
    application.add_handler(CommandHandler("register", lambda update, context: bot.register(update, context, engine, Session)))
    application.add_handler(CommandHandler("mydata", lambda update, context: bot._show_my_data(update, context, engine, Session)))
    application.add_handler(CommandHandler("edit_my_data", bot.edit_my_data))
    application.add_handler(CommandHandler("event_create", lambda update, context: bot.event_create(update, context, engine, Session)))
    application.add_handler(CommandHandler("event_join", lambda update, context: bot.event_join(update, context, engine, Session)))
    application.add_handler(CommandHandler("event_list", lambda update, context: bot.event_list(update, context, engine, Session)))
    application.add_handler(CommandHandler("balance_teams", lambda update, context: bot.balance_teams_command(update, context, engine, Session)))
    application.add_handler(CallbackQueryHandler(lambda update, context: bot._process_callback_query(update, context, engine, Session)))


@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = f"""
    <html>
    <head>
        <title>Volleyball Bot Status</title>
    </head>
    <body>
        <h1>Volleyball Bot Status</h1>
        <p><strong>Mode:</strong> {MODE}</p>
        <p><strong>Telegram Bot:</strong> {bot_status}</p>
        <p><strong>Database:</strong> {db_status}</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/webhook")
async def webhook(request: Request, session: Session = Depends(get_db_session)):
    """Handle webhook updates."""
    await startup_event()
    await application.initialize()
    try:
        json_str = await request.body()
        json_data = json.loads(json_str.decode("utf-8"))  # Parse JSON data
        update = Update.de_json(json_data, application.bot)

        # Pass the session to the handler
        context = CallbackContext(application)  # Create a context
        context.session = session

        await application.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/favicon.ico")
async def favicon_ico():
    raise HTTPException(status_code=404, detail="Not Found")


@app.get("/favicon.png")
async def favicon_png():
    raise HTTPException(status_code=404, detail="Not Found")


@app.on_event("startup")
async def startup_event():
    """Set up the bot on startup."""
    logger.info(f"Starting bot in {MODE} mode")
    try:
        if MODE == "webhook":
            if not WEBHOOK_URL:
                raise ValueError("WEBHOOK_URL must be set when MODE is webhook")
            logger.info(f"Setting webhook to {WEBHOOK_URL}")
            webhook_result = await application.bot.set_webhook(WEBHOOK_URL)
            if not webhook_result:
                logger.error("Failed to set webhook. Please check the WEBHOOK_URL and bot token.")
                # Consider raising an exception here to prevent the app from starting if the webhook fails to set
            else:
                logger.info("Webhook set successfully.")
        else:
            raise ValueError("MODE must be 'webhook'")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        await application.shutdown()
        logger.info("Bot shutting down")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
