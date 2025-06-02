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

setup_logging()
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.config = Config()
        self.auth_manager = AuthManager(self.config.admin_ids)
        self.user_handlers = UserHandlers()
        self.admin_handlers = AdminHandlers(self.auth_manager)

        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        self.application = Application.builder().token(self.bot_token).build()

    async def setup_handlers(self):
        app = self.application
        app.add_handler(CommandHandler("start", self.user_handlers.start_command))
        app.add_handler(CommandHandler("help", self.user_handlers.help_command))
        app.add_handler(CommandHandler("info", self.user_handlers.info_command))
        app.add_handler(CommandHandler("balance", self.user_handlers.balance_command))

        app.add_handler(CommandHandler("admin", self.admin_handlers.admin_menu))
        app.add_handler(CommandHandler("stats", self.admin_handlers.get_stats))
        app.add_handler(CommandHandler("users", self.admin_handlers.list_users))
        app.add_handler(CommandHandler("broadcast", self.admin_handlers.broadcast_message))
        app.add_handler(CommandHandler("ban", self.admin_handlers.ban_user))
        app.add_handler(CommandHandler("unban", self.admin_handlers.unban_user))
        app.add_handler(CommandHandler("addadmin", self.admin_handlers.add_admin))
        app.add_handler(CommandHandler("removeadmin", self.admin_handlers.remove_admin))
        app.add_handler(CommandHandler("logs", self.admin_handlers.get_logs))

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_error_handler(self.error_handler)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or "No username"
        message_text = update.message.text
        logger.info(f"Message from user {user_id} ({username}): {message_text}")

        self.user_handlers.log_user_activity(user_id, username, message_text)

        if await self.user_handlers.handle_lichess_registration(update, context):
            return

        await update.message.reply_text("تم استلام رسالتك! استخدم /help لرؤية الأوامر المتاحة.")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ حدث خطأ أثناء تنفيذ الطلب. حاول مرة أخرى لاحقًا.")

    async def start_bot(self):
        await self.setup_handlers()
        logger.info("Bot is running with polling...")
        await self.application.run_polling()


async def main():
    bot = TelegramBot()
    try:
        await bot.start_bot()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise