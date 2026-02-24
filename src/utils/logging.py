# src/utils/logging.py
"""
Logging Configuration
===================

Central logging setup for the entire pipeline
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_file: str = None):
    """
    Setup logging configuration.
    
    Args:
        log_file (str, optional): Path to log file. If None, logs to console only.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("VideoFactory")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "VideoFactory"):
    """Get existing logger or create new one."""
    return logging.getLogger(name)

def log_session_start(topic: str, session_id: str):
    """Log session start."""
    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🎬 SESSION STARTED")
    logger.info(f"📅 Date: {datetime.now().isoformat()}")
    logger.info(f"🎯 Topic: {topic}")
    logger.info(f"🆔 Session ID: {session_id}")
    logger.info("=" * 60)

def log_session_end(session_id: str, status: str, details: dict = None):
    """Log session end."""
    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🏁 SESSION ENDED")
    logger.info(f"🆔 Session ID: {session_id}")
    logger.info(f"✅ Status: {status}")
    if details:
        for key, value in details.items():
            logger.info(f"   {key}: {value}")
    logger.info("=" * 60)

def log_error(error: Exception, context: str = ""):
    """Log error with context."""
    logger = get_logger()
    logger.error(f"❌ ERROR in {context}: {str(error)}")
    logger.exception("Full traceback:")

def log_progress(current: int, total: int, task: str = ""):
    """Log progress percentage."""
    logger = get_logger()
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"📊 Progress: {current}/{total} ({percentage:.1f}%) - {task}")
