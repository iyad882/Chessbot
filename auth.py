"""
Authentication utilities for the Telegram bot
Handles admin verification and access control
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, admin_ids: list = None):
        from config import Config
        self.config = Config()
        if admin_ids:
            self.config.admin_ids = admin_ids

    def is_admin(self, user_id: int) -> bool:
        """Check if user is an administrator"""
        return user_id in self.config.admin_ids

    def is_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        return user_id in self.config.banned_users

    async def check_admin_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Check if user has admin access and send appropriate response if not
        Returns True if user is admin, False otherwise
        """
        user = update.effective_user
        user_id = user.id
        username = user.username or "No username"

        # Check if user is banned
        if self.is_banned(user_id):
            logger.warning(f"Banned user {user_id} ({username}) attempted to use admin command")
            await update.message.reply_text(
                "🚫 You are banned from using this bot."
            )
            return False

        # Check if user is admin
        if not self.is_admin(user_id):
            logger.warning(f"Non-admin user {user_id} ({username}) attempted to use admin command")
            await update.message.reply_text(
                "❌ This command is only available to administrators.\n"
                "If you believe this is an error, please contact an administrator."
            )
            return False

        # Log admin action
        command = update.message.text.split()[0] if update.message.text else "unknown"
        logger.info(f"Admin {user_id} ({username}) executed command: {command}")
        
        return True

    def require_admin(self, func):
        """
        Decorator to require admin access for a function
        Usage: @auth_manager.require_admin
        """
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if await self.check_admin_access(update, context):
                return await func(update, context)
            return None
        return wrapper

    def get_admin_list(self) -> list:
        """Get list of admin IDs"""
        return self.config.admin_ids.copy()

    def get_banned_list(self) -> list:
        """Get list of banned user IDs"""
        return self.config.banned_users.copy()

    def add_admin(self, user_id: int) -> bool:
        """Add a new admin"""
        return self.config.add_admin(user_id)

    def remove_admin(self, user_id: int) -> bool:
        """Remove an admin"""
        return self.config.remove_admin(user_id)

    def ban_user(self, user_id: int) -> bool:
        """Ban a user"""
        return self.config.ban_user(user_id)

    def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        return self.config.unban_user(user_id)

    def get_user_status(self, user_id: int) -> str:
        """Get user status (admin, banned, or regular)"""
        if self.is_admin(user_id):
            return "admin"
        elif self.is_banned(user_id):
            return "banned"
        else:
            return "regular"

    def format_user_info(self, user_id: int, username: str = None) -> str:
        """Format user information with status"""
        status = self.get_user_status(user_id)
        status_emoji = {
            "admin": "👑",
            "banned": "🚫",
            "regular": "👤"
        }
        
        user_info = f"{status_emoji[status]} {user_id}"
        if username:
            user_info += f" (@{username})"
        
        return user_info

    def log_security_event(self, event_type: str, user_id: int, details: str = ""):
        """Log security-related events"""
        logger.warning(f"SECURITY {event_type}: User {user_id} - {details}")
