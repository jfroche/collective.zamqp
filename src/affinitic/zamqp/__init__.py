import logging
from logging.handlers import TimedRotatingFileHandler
LOGGER = 'affinitic.zamqp'
logger = logging.getLogger(LOGGER)
logger.setLevel(logging.DEBUG)
fh = TimedRotatingFileHandler("amqp.log", 'midnight', 1)
fh.suffix = "%Y-%m-%d-%H-%M"
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
