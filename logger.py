# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

import logging
from logging.handlers import RotatingFileHandler

SHORT_LOG_FORMAT = "[%(asctime)s - %(levelname)s] - %(name)s - %(message)s"
FULL_LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s (%(filename)s:%(lineno)d)"

logging.basicConfig(
    level=logging.DEBUG,  # More verbose for better debugging
    format=SHORT_LOG_FORMAT,
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=5 * 1024 * 1024, backupCount=10),
        logging.StreamHandler()
    ]
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
