import os
import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv
from utils.db import create_db_engine, create_db_session
from bot import (
    start,
    register,
    _ask_question,
    _save_responses,
    _show_my_data,
    edit_my_data,
    _process_callback_query,
    event_create,
    event_join,
    event_list,
    balance_teams_command,
)  # Import the handler functions

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_IDS = [
    int(admin_id) for admin_id in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
]
MODE = os.environ.get("MODE", "polling")  # Default to polling if not specified
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize Telegram bot application
bot_status = "Not Initialized"
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
    bot_status = "Error: TELEGRAM_BOT_TOKEN not found"
else:
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
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


# Register Telegram handlers
application.add_handler(CommandHandler("start", lambda update, context: start(update, context, engine, Session)))
application.add_handler(CommandHandler("register", lambda update, context: register(update, context, engine, Session)))
application.add_handler(CommandHandler("mydata", lambda update, context: _show_my_data(update, context, engine, Session)))
application.add_handler(CommandHandler("edit_my_data", edit_my_data))
application.add_handler(CommandHandler("event_create", lambda update, context: event_create(update, context, engine, Session)))
application.add_handler(CommandHandler("event_join", lambda update, context: event_join(update, context, engine, Session)))
application.add_handler(CommandHandler("event_list", lambda update, context: event_list(update, context, engine, Session)))
application.add_handler(CommandHandler("balance_teams", lambda update, context: balance_teams_command(update, context, engine, Session)))
application.add_handler(CallbackQueryHandler(lambda update, context: _process_callback_query(update, context, engine, Session)))


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
async def webhook(request: Request):
    """Handle webhook updates."""
    try:
        json_str = await request.body()
        update = Update.de_json(json_str.decode("utf-8"), application.bot)
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
            await application.bot.set_webhook(WEBHOOK_URL)
        elif MODE == "polling":
            logger.info("Starting polling")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        else:
            raise ValueError("MODE must be either 'webhook' or 'polling'")

        # Initialize database (example)
        # from utils.db import init_db
        # init_db(engine)
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
