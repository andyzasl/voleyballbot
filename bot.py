import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from utils.db import create_db_engine, create_db_session, load_questions
from utils.team_balancer import balance_teams
from models import Player, Question, QuestionOption, Response, Event, EventParticipant

# Load config
with open('config.json') as f:
    config = json.load(f)

# Database connection
engine = create_db_engine(config)
Session = create_db_session(engine)
session = Session()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    context.bot.send_message(chat_id=update.effective_chat.id,
                           text="Welcome to the Volleyball Bot!\n"
                                "Type /register to join our community!")

def register(update: Update, context: CallbackContext):
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

    context.user_data['current_question'] = 1  # Start with the first question
    _ask_question(update, context)

def _ask_question(update: Update, context: CallbackContext):
    """Asks a question from the survey."""
    chat_id = update.effective_chat.id
    question_id = context.user_data.get('current_question')
    session = Session()

    question = session.query(Question).get(question_id)
    if not question:
        session.close()
        _save_responses(update, context)
        return

    keyboard = [[InlineKeyboardButton(option.option_text, callback_data=str(option.id))] for option in question.options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=chat_id, text=question.question_text, reply_markup=reply_markup)
    session.close()

def _save_responses(update: Update, context: CallbackContext):
    """Saves the responses and calculates the player's power level."""
    chat_id = update.effective_chat.id
    session = Session()
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()

    # Calculate total score based on responses
    total_score = 0
    if 'responses' in context.user_:
        for response_id in context.user_data.get('responses', {}).values():
            option = session.query(QuestionOption).get(response_id)
            if option:
                total_score += option.response_points

    # Update player's skill_level (you might want a more sophisticated calculation)
    player.skill_level = total_score  # Assuming you add a 'skill_level' column to the Player model

    session.commit()
    session.close()

    context.bot.send_message(chat_id=chat_id, text="Thank you for completing the survey!")
    # Clean up user_data
    context.user_data.pop('current_question', None)
    context.user_data.pop('responses', None)

def _show_my_data(update: Update, context: CallbackContext):
    """Show user's data."""
    session = Session()
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()
    session.close()

    if player:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Telegram Handle: {player.telegram_handle}\n"
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You haven't registered yet. Use /register to join!"
        )

def edit_my_data(update: Update, context: CallbackContext):
    """Allows the user to edit their data."""
    # Implement the logic to allow the user to edit their data
    # This could involve asking questions and updating the database
    context.bot.send_message(chat_id=update.effective_chat.id, text="This feature is not yet implemented.")

def _process_callback_query(update: Update, context: CallbackContext):
    """Processes the callback query from the inline keyboard."""
    query = update.callback_query
    query.answer()

    option_id = int(query.data)
    question_id = context.user_data.get('current_question')
    player_id = update.effective_user.id

    session = Session()
    player = session.query(Player).filter_by(telegram_id=player_id).first()
    option = session.query(QuestionOption).get(option_id)

    if not player or not option:
        session.close()
        query.edit_message_text(text="An error occurred. Please try again.")
        return

    # Store the response
    if 'responses' not in context.user_:
        context.user_data['responses'] = {}
    context.user_data['responses'][question_id] = option_id

    # Move to the next question
    context.user_data['current_question'] = question_id + 1
    session.close()
    _ask_question(update, context)

def event_create(update: Update, context: CallbackContext):
    """Creates a new event (Admin only)."""
    # Implement admin check here
    if update.effective_user.id not in config['admin_telegram_ids']:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not authorized to use this command.")
        return

    # Get event details from the context (you'll need to implement a conversation handler for this)
    # For simplicity, let's assume the event details are passed as arguments
    try:
        name = context.args[0]
        description = context.args[1]
        limit = int(context.args[2])
    except (IndexError, ValueError):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /event_create <name> <description> <limit>")
        return

    session = Session()
    event = Event(name=name, description=description, max_participants=limit)
    session.add(event)
    session.commit()
    session.close()

    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Event '{name}' created successfully.")

def event_join(update: Update, context: CallbackContext):
    """Allows a player to join an event."""
    try:
        event_id = int(context.args[0])
    except (IndexError, ValueError):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /event_join <event_id>")
        return

    session = Session()
    event = session.query(Event).get(event_id)
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()

    if not event or not player:
        session.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Event or player not found.")
        return

    # Check if the player is already participating
    if session.query(EventParticipant).filter_by(event_id=event_id, player_id=player.id).first():
        session.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are already participating in this event.")
        return

    # Check if the event is full
    if len(event.participants) >= event.max_participants:
        session.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text="This event is full.")
        return

    participant = EventParticipant(event_id=event_id, player_id=player.id)
    session.add(participant)
    session.commit()
    session.close()

    context.bot.send_message(chat_id=update.effective_chat.id, text="You have successfully joined the event!")

def event_list(update: Update, context: CallbackContext):
    """Lists available events."""
    session = Session()
    events = session.query(Event).all()
    session.close()

    if not events:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No events found.")
        return

    message = "Available Events:\n"
    for event in events:
        message += f"- {event.name} (ID: {event.id})\n"

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def balance_teams_command(update: Update, context: CallbackContext):
    """Balances teams for a specific event (Admin only)."""
    # Implement admin check here
    if update.effective_user.id not in config['admin_telegram_ids']:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not authorized to use this command.")
        return

    try:
        event_id = int(context.args[0])
    except (IndexError, ValueError):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /balance_teams <event_id>")
        return

    session = Session()
    event = session.query(Event).get(event_id)

    if not event:
        session.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Event not found.")
        return

    participants = [participant.player for participant in event.participants]
    try:
        teams = balance_teams(participants)
    except ValueError as e:
        session.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
        return

    message = "Balanced Teams:\n"
    for i, team in enumerate(teams):
        message += f"Team {i + 1}:\n"
        for player in team:
            message += f"  - {player.telegram_handle}\n"

    session.close()
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(config['bot_token'], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register commands
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('register', register))
    dp.add_handler(CommandHandler('mydata', lambda update, ctx: _show_my_data(update, ctx)))
    dp.add_handler(CommandHandler('edit_my_data', edit_my_data))
    dp.add_handler(CommandHandler('event_create', event_create))
    dp.add_handler(CommandHandler('event_join', event_join))
    dp.add_handler(CommandHandler('event_list', event_list))
    dp.add_handler(CommandHandler('balance_teams', balance_teams_command))

    # Register callback query handler
    dp.add_handler(CallbackQueryHandler(_process_callback_query))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
