import logging
import os
from pathlib import Path
from typing import Optional

from config.settings import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Configure logging for the application."""

    level = log_level or settings.log_level
    file_path = log_file or settings.log_file

    # Create logs directory if it doesn't exist
    log_dir = Path(file_path).parent
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Create application logger
    logger = logging.getLogger("intelligent_agent")

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"intelligent_agent.{name}")