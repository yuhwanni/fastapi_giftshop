import logging
import os
from datetime import date
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# Setting formatter for log messages
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# File Handler
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, f"{date.today()}.log"),
    when="midnight",
    interval=1,
    encoding="utf-8",
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Reset handlers to avoid duplicate logs
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

logger.debug("This is a DEBUG message.")
logger.info("Logging setup complete.")