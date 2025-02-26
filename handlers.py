import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from models import Player, Question, QuestionOption, Response, Event, EventParticipant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext, engine, Session):
    """Send a message when the command /start is issued."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to the Volleyball Bot!\n" "Type /register to join our community!",
    )


async def register(update: Update, context: CallbackContext, engine, Session):
    """Start the registration process."""
    chat_id = update.effective_chat.id
    telegram_id = update.effective_user.id
    telegram_handle = update.effective_user.username

    session = Session()
    player = session.query(Player).filter_by(telegram_id=telegram_id).first()

    if player:
        session.close()
        await context.bot.send_message(chat_id=chat_id, text="You are already registered!")
        return

    player = Player(telegram_id=telegram_id, telegram_handle=telegram_handle)
    session.add(player)
    session.commit()
    session.close()

    context.user_data["current_question"] = 1  # Start with the first question
    await _ask_question(update, context, engine, Session)


async def _ask_question(update: Update, context: CallbackContext, engine, Session):
    """Asks a question from the survey."""
    chat_id = update.effective_chat.id
    question_id = context.user_data.get("current_question")
    session = Session()

    question = session.query(Question).get(question_id)
    if not question:
        session.close()
        await _save_responses(update, context, engine, Session)
        return

    keyboard = [[InlineKeyboardButton(option.option_text, callback_data=str(option.id))] for option in question.options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id, text=question.question_text, reply_markup=reply_markup
    )
    session.close()


async def _save_responses(update: Update, context: CallbackContext, engine, Session):
    """Saves the responses and calculates the player's power level."""
    chat_id = update.effective_chat.id
    session = Session()
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()

    # Calculate total score based on responses
    total_score = 0
    if "responses" in context.user_:
        for response_id in context.user_data.get("responses", {}).values():
            option = session.query(QuestionOption).get(option_id)
            if option:
                total_score += option.response_points

    # Update player's skill_level (you might want a more sophisticated calculation)
    player.skill_level = (
        total_score  # Assuming you add a 'skill_level' column to the Player model
    )

    session.commit()
    session.close()

    await context.bot.send_message(
        chat_id=chat_id, text="Thank you for completing the survey!"
    )
    # Clean up user_data
    context.user_data.pop("current_question", None)
    context.user_data.pop("responses", None)


async def _show_my_data(update: Update, context: CallbackContext, engine, Session):
    """Show user's data."""
    session = Session()
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()
    session.close()

    if player:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Telegram Handle: {player.telegram_handle}\n",
        )
    else:
        await context.bot.send_message(
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


async def _process_callback_query(update: Update, context: CallbackContext, engine, Session):
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
    await _ask_question(update, context, engine, Session)


async def event_create(update: Update, context: CallbackContext, engine, Session):
    """Creates a new event (Admin only)."""
    admin_telegram_ids = [
        int(admin_id)
        for admin_id in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
    ]
    if update.effective_user.id not in admin_telegram_ids:
        await context.bot.send_message(
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
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /event_create <name> <description> <limit>",
        )
        return

    session = Session()
    event = Event(name=name, description=description, max_participants=limit)
    session.add(event)
    session.commit()
    session.close()

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Event '{name}' created successfully.")


async def event_join(update: Update, context: CallbackContext, engine, Session):
    """Allows a player to join an event."""
    try:
        event_id = int(context.args[0])
    except (IndexError, ValueError):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Usage: /event_join <event_id>"
        )
        return

    session = Session()
    event = session.query(Event).get(event_id)
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()

    if not event or not player:
        session.close()
        await context.bot.send_message(
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
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are already participating in this event.",
        )
        return

    # Check if the event is full
    if len(event.participants) >= event.max_participants:
        session.close()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="This event is full."
        )
        return

    participant = EventParticipant(event_id=event_id, player_id=player.id)
    session.add(participant)
    session.commit()
    session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="You have successfully joined the event!"
    )


async def balance_teams_command(update: Update, context: CallbackContext, engine, Session):
    """Balances teams for a specific event (Admin only)."""
    admin_telegram_ids = [
        int(admin_id)
        for admin_id in os.environ.get("ADMIN_TELEGRAM_IDS", "").split(",")
    ]
    if update.effective_user.id not in admin_telegram_ids:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not authorized to use this command.",
        )
        return
