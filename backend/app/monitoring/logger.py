import sys
from loguru import logger

logger.remove()

logger.add(sys.stdout, level="INFO", serialize=True)
logger.add("logs/app.log", level="DEBUG", rotation="100 MB", retention="7 days", serialize=True)
