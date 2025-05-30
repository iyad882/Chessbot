ه#!/usr/bin/env python3
"""
Telegram Bot with Admin Functionality
Main bot application file that initializes the bot and registers handlers
"""

import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config
from handlers.user_handlers import UserHandlers
from handlers.admin_handlers import AdminHandlers
from utils.logging_config import setup_logging
from utils.auth import AuthManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.config = Config()
        self.auth_manager = AuthManager(self.config.admin_ids)
        self.user_handlers = UserHandlers()
        self.admin_handlers = AdminHandlers(self.auth_manager)
        
        # Get bot token from environment variable
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        self.application = None

    async def setup_handlers(self):
        """Setup all command and message handlers"""
        app = self.application
        
        # User commands (available to all users)
        app.add_handler(CommandHandler("start", self.user_handlers.start_command))
        app.add_handler(CommandHandler("help", self.user_handlers.help_command))
        app.add_handler(CommandHandler("info", self.user_handlers.info_command))
        app.add_handler(CommandHandler("balance", self.user_handlers.balance_command))
        
        # Admin commands (restricted to admins only)
        app.add_handler(CommandHandler("admin", self.admin_handlers.admin_menu))
        app.add_handler(CommandHandler("stats", self.admin_handlers.get_stats))
        app.add_handler(CommandHandler("users", self.admin_handlers.list_users))
        app.add_handler(CommandHandler("broadcast", self.admin_handlers.broadcast_message))
        app.add_handler(CommandHandler("ban", self.admin_handlers.ban_user))
        app.add_handler(CommandHandler("unban", self.admin_handlers.unban_user))
        app.add_handler(CommandHandler("addadmin", self.admin_handlers.add_admin))
        app.add_handler(CommandHandler("removeadmin", self.admin_handlers.remove_admin))
        app.add_handler(CommandHandler("logs", self.admin_handlers.get_logs))
        
        # Message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        app.add_error_handler(self.error_handler)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "No username"
        message_text = update.message.text
        
        logger.info(f"Message from user {user_id} ({username}): {message_text}")
        
        # Log user activity
        self.user_handlers.log_user_activity(user_id, username, message_text)
        
        # Check if user is in Lichess registration process
        if await self.user_handlers.handle_lichess_registration(update, context):
            return  # Message was handled by registration process
        
        # Simple echo response for regular messages
        await update.message.reply_text(
            "تم استلام رسالتك! استخدم /help لرؤية الأوامر المتاحة."
        )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred while processing your request. Please try again later."
            )

    async def start_bot(self):
        """Start the bot"""
        try:
            self.application = Application.builder().token(self.bot_token).build()
            
            await self.setup_handlers()
            
            logger.info("Bot is starting...")
            await self.application.initialize()
            await self.application.start()
            
            logger.info("Bot is running! Press Ctrl+C to stop.")
            await self.application.updater.start_polling()
            
            # Keep the bot running
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
        finally:
            if self.application:
                await self.application.stop()

async def main():
    """Main function to run the bot"""
    bot = TelegramBot()
    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

if __name__ == "__main__":
    import threading
import socket

# فتح منفذ وهمي لإرضاء Render
def fake_web_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 10000))  # منفذ وهمي
    s.listen(1)
    while True:
        conn, addr = s.accept()
        conn.send(b'HTTP/1.1 200 OK\n\nHello from Telegram bot!')
        conn.close()

threading.Thread(target=fake_web_server, daemon=True).start()
asyncio.run(main())
