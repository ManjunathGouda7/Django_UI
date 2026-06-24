import logging,os
from datetime import datetime

os.makedirs("assets/logs", exist_ok=True)
LOG_FILE = datetime.now().strftime("assets/logs/automation_%Y%m%d_%H%M%S.log")
logger = logging.getLogger("AutomationFramework")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    # File Handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)