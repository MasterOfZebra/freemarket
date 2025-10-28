"""
Logging configuration
"""
import logging
from backend.config import LOG_LEVEL, LOG_FORMAT


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
    )
    return logging.getLogger(__name__)


def get_logger(name: str):
    """Get a logger instance"""
    return logging.getLogger(name)
