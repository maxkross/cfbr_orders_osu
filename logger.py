from constants import LOG_FILE
import logging

class Logger:
    @staticmethod
    def log(log_line):
        with open(LOG_FILE, "a") as file:
            file.write(log_line + '\n')

    @staticmethod
    def init_logging():
        logging.basicConfig(
            filename=LOG_FILE,
            format='%(asctime)s: %(levelname)s:%(name)s -- %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.INFO
            )

    @staticmethod
    def getLogger(name):
        return logging.getLogger(name)