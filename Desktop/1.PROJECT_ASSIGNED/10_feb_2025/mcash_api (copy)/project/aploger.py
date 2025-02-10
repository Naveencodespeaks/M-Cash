import os
import logging
import logging.config
import configparser
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


config = configparser.ConfigParser()
config.read('logging_config.ini')
log_filename = datetime.now().strftime('%Y-%m-%d') + '.log'
log_folder = 'logs/'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

log_file_path = os.path.join(log_folder, log_filename)
config.set('handler_file_handler', 'args', f"('{log_file_path}', 'midnight', 1, 7)")

logging.config.fileConfig(config)
AppLogger = logging.getLogger('root')
