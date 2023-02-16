from constants import LOG_FILE


class Logger:
    @staticmethod
    def log(log_line):
        with open(LOG_FILE, "a") as file:
            file.write(log_line + '\n')
