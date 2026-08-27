"""
Logging Module for Bank Management System.
Configures file and console logging without leaking sensitive information.
"""

import logging
import sys
from config import LOG_FILE

# Configure application logger
_logger = logging.getLogger("BankManagementSystem")
_logger.setLevel(logging.INFO)

# File handler for audit logs
if not _logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    _logger.addHandler(file_handler)

def get_logger() -> logging.Logger:
    """Returns the configured application logger instance."""
    return _logger

def log_event(event_type: str, details: str, level: str = "INFO"):
    """
    Helper to log system events securely.
    
    Args:
        event_type: Short identifier of the event (e.g., 'AUTH_LOGIN_SUCCESS', 'DEPOSIT')
        details: Safe details string (no passwords)
        level: Log level ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    message = f"[{event_type}] {details}"
    if level == "INFO":
        _logger.info(message)
    elif level == "WARNING":
        _logger.warning(message)
    elif level == "ERROR":
        _logger.error(message)
    elif level == "CRITICAL":
        _logger.critical(message)
    else:
        _logger.debug(message)
