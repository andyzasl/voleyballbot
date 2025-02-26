import logging
import os
from fastapi import FastAPI
from telegram import Bot
from telegram.ext import Application

logger = logging.getLogger(__name__)

async def startup_event(app: FastAPI, TELEGRAM_BOT_TOKEN: str, WEBHOOK_URL: str, application: Application):
    """Set up the bot on startup."""
    logger.info(f"Starting bot in webhook mode")
    try:
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL must be set when MODE is webhook")
        logger.info(f"Setting webhook to {WEBHOOK_URL}")
        webhook_result = await application.bot.set_webhook(WEBHOOK_URL)
        if not webhook_result:
            logger.error("Failed to set webhook. Please check the WEBHOOK_URL and bot token.")
            # Consider raising an exception here to prevent the app from starting if the webhook fails to set
        else:
            logger.info("Webhook set successfully.")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

async def shutdown_event(app: FastAPI, application: Application):
    """Clean up resources on shutdown."""
    try:
        await application.shutdown()
        logger.info("Bot shutting down")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
