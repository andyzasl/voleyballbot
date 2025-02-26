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
import handlers  # Import the handler functions
from startup import startup_event, shutdown_event

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
    application.add_handler(CommandHandler("start", lambda update, context: handlers.start(update, context, engine, Session)))
    application.add_handler(CommandHandler("register", lambda update, context: handlers.register(update, context, engine, Session)))
    application.add_handler(CommandHandler("mydata", lambda update, context: handlers._show_my_data(update, context, engine, Session)))
    application.add_handler(CommandHandler("edit_my_data", handlers.edit_my_data))
    application.add_handler(CommandHandler("event_create", lambda update, context: handlers.event_create(update, context, engine, Session)))
    application.add_handler(CommandHandler("event_join", lambda update, context: handlers.event_join(update, context, engine, Session)))
    application.add_handler(CommandHandler("event_list", lambda update, context: handlers.event_list(update, context, engine, Session)))
    application.add_handler(CommandHandler("balance_teams", lambda update, context: handlers.balance_teams_command(update, context, engine, Session)))
    application.add_handler(CallbackQueryHandler(lambda update, context: handlers._process_callback_query(update, context, engine, Session)))


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
async def startup_event_handler():
    """Set up the bot on startup."""
    await startup_event(app, TELEGRAM_BOT_TOKEN, WEBHOOK_URL, application)


@app.on_event("shutdown")
async def shutdown_event_handler():
    """Clean up resources on shutdown."""
    await shutdown_event(app, application)


def start(update: Update, context: CallbackContext, engine, Session):
    """Send a message when the command /start is issued."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to the Volleyball Bot!\n" "Type /register to join our community!",
    )


def register(update: Update, context: CallbackContext, engine, Session):
    """Start the registration process."""
    chat_id = update.effective_chat.id
    telegram_id = update.effective_user.id
    telegram_handle = update.effective_user.username

    session = Session()
    player = session.query(Player).filter_by(telegram_id=telegram_id).first()

    if player:
        session.close()
        context.bot.send_message(chat_id=chat_id, text="You are already registered!")
        return

    player = Player(telegram_id=telegram_id, telegram_handle=telegram_handle)
    session.add(player)
    session.commit()
    session.close()

    context.user_data["current_question"] = 1  # Start with the first question
    _ask_question(update, context, engine, Session)


def _ask_question(update: Update, context: CallbackContext, engine, Session):
    """Asks a question from the survey."""
    chat_id = update.effective_chat.id
    question_id = context.user_data.get("current_question")
    session = Session()

    question = session.query(Question).get(question_id)
    if not question:
        session.close()
        _save_responses(update, context, engine, Session)
        return

    keyboard = [[InlineKeyboardButton(option.option_text, callback_data=str(option.id))] for option in question.options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=chat_id, text=question.question_text, reply_markup=reply_markup
    )
    session.close()


def _save_responses(update: Update, context: CallbackContext, engine, Session):
    """Saves the responses and calculates the player's power level."""
    chat_id = update.effective_chat.id
    session = Session()
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()

    # Calculate total score based on responses
    total_score = 0
    if "responses" in context.user_:
        for response_id in context.user_data.get("responses", {}).values():
            option = session.query(QuestionOption).get(response_id)
            if option:
                total_score += option.response_points

    # Update player's skill_level (you might want a more sophisticated calculation)
    player.skill_level = (
        total_score  # Assuming you add a 'skill_level' column to the Player model
    )

    session.commit()
    session.close()

    context.bot.send_message(
        chat_id=chat_id, text="Thank you for completing the survey!"
    )
    # Clean up user_data
    context.user_data.pop("current_question", None)
    context.user_data.pop("responses", None)


def _show_my_data(update: Update, context: CallbackContext, engine, Session):
    """Show user's data."""
    session = Session()
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()
    session.close()

    if player:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Telegram Handle: {player.telegram_handle}\n",
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You haven't registered yet. Use /register to join!",
        )


def edit_my_data(update: Update, context: CallbackContext):
    """Allows the user to edit their data."""
    # Implement the logic to allow the user to edit their data
    # This could involve asking questions and updating the database
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="This feature is not yet implemented."
    )


def _process_callback_query(update: Update, context: CallbackContext, engine, Session):
    """Processes the callback query from the inline keyboard."""
    query = update.callback_query
    query = update.callback_query
    query.answer()

    option_id = int(query.data)
    question_id = context.user_data.get("current_question")
    player_id = update.effective_user.id

    session = Session()
    player = session.query(Player).filter_by(telegram_id=player_id).first()
    option = session.query(QuestionOption).get(option_id)

    if not player or not option:
        session.close()
        query.edit_message_text(text="An error occurred. Please try again.")
        return

    # Store the response
    if "responses" not in context.user_:
        context.user_data["responses"] = {}
        context.user_data["responses"][question_id] = option_id

    # Move to the next question
    context.user_data["current_question"] = question_id + 1
    session.close()
    _ask_question(update, context, engine, Session)


def event_create(update: Update, context: CallbackContext, engine, Session):
    """Creates a new event (Admin only)."""
    admin_telegram_ids = [
        int(admin_id)
        for admin_id in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
    ]
    if update.effective_user.id not in admin_telegram_ids:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not authorized to use this command.",
        )
        return

    # Get event details from the context (you'll need to implement a conversation handler for this)
    # For simplicity, let's assume the event details are passed as arguments
    try:
        name = context.args[0]
        description = context.args[1]
        limit = int(context.args[2])
    except (IndexError, ValueError):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /event_create <name> <description> <limit>",
        )
        return

    session = Session()
    event = Event(name=name, description=description, max_participants=limit)
    session.add(event)
    session.commit()
    session.close()

    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Event '{name}' created successfully.")


def event_join(update: Update, context: CallbackContext, engine, Session):
    """Allows a player to join an event."""
    try:
        event_id = int(context.args[0])
    except (IndexError, ValueError):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Usage: /event_join <event_id>"
        )
        return

    session = Session()
    event = session.query(Event).get(event_id)
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()

    if not event or not player:
        session.close()
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Event or player not found."
        )
        return

    # Check if the player is already participating
    if (
        session.query(EventParticipant)
        .filter_by(event_id=event_id, player_id=player.id)
        .first()
    ):
        session.close()
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are already participating in this event.",
        )
        return

    # Check if the event is full
    if len(event.participants) >= event.max_participants:
        session.close()
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="This event is full."
        )
        return

    participant = EventParticipant(event_id=event_id, player_id=player.id)
    session.add(participant)
    session.commit()
    session.close()

    context.bot.send_message(
        chat_id=update.effective_chat.id, text="You have successfully joined the event!"
    )


def balance_teams_command(update: Update, context: CallbackContext, engine, Session):
    """Balances teams for a specific event (Admin only)."""


