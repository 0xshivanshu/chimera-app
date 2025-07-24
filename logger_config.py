import logging
import sys
from config import LOG_LEVEL

def setup_logging():
    """Configures a centralized logger for the application."""
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(LOG_LEVEL)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    file_handler = logging.FileHandler('chimera.log')
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    module_logger = logging.getLogger(__name__)
    return module_logger

log = setup_logging()