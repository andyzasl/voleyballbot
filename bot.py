import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
from models import Player, Question, Event, EventParticipant

# Load config
with open('config.json') as f:
    config = json.load(f)

# Database connection
engine = create_engine(config['database_url'])
Session = sessionmaker(bind=engine)
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
    # Initialize player data if new
    player = Player(telegram_id=update.effective_user.id)
    session.add(player)
    session.commit()
    
    # Start the survey
    context.bot.send_message(chat_id=update.effective_chat.id,
                           text="Let's get to know you better!")
    
    # Ask first question
    _ask_question(update, context, 1)

def _ask_question(update: Update, context: CallbackContext, question_id: int):
    """Helper function to ask survey questions."""
    question = session.query(Question).get(question_id)
    if not question:
        _save_responses(update, context)
        return
        
    context.bot.send_message(chat_id=update.effective_chat.id,
                           text=question.question_text,
                           reply_markup=None)

def _save_responses(update: Update, context: CallbackContext):
    """Save all responses and calculate player's power level."""
    pass  # To be implemented

def _show_my_data(update: Update, context: CallbackContext):
    """Show user's data."""
    player = session.query(Player).filter_by(telegram_id=update.effective_user.id).first()
    if player:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Name: {player.name}\n"
                 f"Experience: {player.experience}\n"
                 f"Position: {player.position}\n"
                 f"Power: {player.power}"
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You haven't registered yet. Use /register to join!"
        )

def _process_message(update: Update, context: CallbackContext):
    """Process incoming messages during registration."""
    pass  # To be implemented

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(config['bot_token'], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register commands
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('register', register))
    dp.add_handler(CommandHandler('mydata', lambda update, ctx: _show_my_data(update, ctx)))
    
    # Register message handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, ctx: _process_message(update, ctx)))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
