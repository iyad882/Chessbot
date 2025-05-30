"""
Logging configuration for the Telegram bot
Sets up structured logging with appropriate levels and formatting
"""

import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_file: str = "bot.log"):
    """
    Setup logging configuration for the bot
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    """
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "."
    if log_dir != "." and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        root_logger.warning(f"Could not setup file logging: {e}")
    
    # Reduce verbosity of some third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log startup message
    logging.info("=" * 50)
    logging.info(f"Bot logging initialized at {datetime.now()}")
    logging.info(f"Log level: {log_level}")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 50)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_user_action(user_id: int, username: str, action: str, details: str = ""):
    """
    Log user actions with consistent formatting
    
    Args:
        user_id: Telegram user ID
        username: Telegram username
        action: Action performed
        details: Additional details
    """
    logger = logging.getLogger("user_actions")
    message = f"User {user_id} (@{username}) - {action}"
    if details:
        message += f" - {details}"
    logger.info(message)

def log_admin_action(admin_id: int, admin_username: str, action: str, target: str = "", details: str = ""):
    """
    Log admin actions with consistent formatting
    
    Args:
        admin_id: Admin user ID
        admin_username: Admin username
        action: Action performed
        target: Target of the action (user ID, etc.)
        details: Additional details
    """
    logger = logging.getLogger("admin_actions")
    message = f"Admin {admin_id} (@{admin_username}) - {action}"
    if target:
        message += f" - Target: {target}"
    if details:
        message += f" - {details}"
    logger.info(message)

def log_security_event(event_type: str, user_id: int, username: str, details: str = ""):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        user_id: User ID involved
        username: Username involved
        details: Event details
    """
    logger = logging.getLogger("security")
    message = f"SECURITY {event_type}: User {user_id} (@{username})"
    if details:
        message += f" - {details}"
    logger.warning(message)

def log_error(error: Exception, context: str = ""):
    """
    Log errors with consistent formatting
    
    Args:
        error: Exception that occurred
        context: Context where error occurred
    """
    logger = logging.getLogger("errors")
    message = f"ERROR in {context}: {type(error).__name__}: {str(error)}"
    logger.error(message, exc_info=True)

class BotLogger:
    """
    Centralized logger class for the bot with convenience methods
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def user_action(self, user_id: int, username: str, action: str, details: str = ""):
        """Log user action"""
        log_user_action(user_id, username, action, details)
    
    def admin_action(self, admin_id: int, admin_username: str, action: str, target: str = "", details: str = ""):
        """Log admin action"""
        log_admin_action(admin_id, admin_username, action, target, details)
    
    def security_event(self, event_type: str, user_id: int, username: str, details: str = ""):
        """Log security event"""
        log_security_event(event_type, user_id, username, details)
