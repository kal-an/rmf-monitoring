import logging
from logging.handlers import TimedRotatingFileHandler


def setup_log(logger_name: str, file_name: str, log_level: int=logging.DEBUG, backup_count: int=7):
    log = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = TimedRotatingFileHandler(file_name, when="midnight", backupCount=backup_count)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    log.addHandler(file_handler)
    return log
