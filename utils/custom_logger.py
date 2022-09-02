import asyncio
import logging
from datetime import datetime
from os import makedirs

from utils.root import get_project_root
from utils.terminal import update_title


LOGGING_LEVEL = logging.DEBUG  # @todo - change this in production to .INFO, maybe

class Log:
    def __init__(self, fmt: str = '[ACC CREATE]', do_update_title: bool = True):
        self.fmt = fmt.rjust(15)
        self.do_update_title = do_update_title

    def update_title(self, text):
        if self.do_update_title:
            update_title(f'{self.fmt}: {text}')

    def info(self, text): logger().info(f'{self.fmt}: {text}') or self.update_title(f'{self.fmt}: {text}')
    def warn(self, text): logger().warning(f'{self.fmt}: {text}') or self.update_title(f'{self.fmt}: {text}')
    def debug(self, text): logger().debug(f'{self.fmt}: {text}') or self.update_title(f'{self.fmt}: {text}')
    def error(self, text): logger().error(f'{self.fmt}: {text}') or self.update_title(f'{self.fmt}: {text}')
    def exception(self, text): logger().exception(f'{self.fmt}: {text}')


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;1m"
    bright_green = "\u001b[32;1m"
    yellow = "\x1b[33;1m"
    red = "\u001b[31m"
    bold_red = "\x1b[31"
    reset = "\x1b[0m"
    green = "\u001b[32m"
    bright_magenta = "\u001b[35;1m"
    format = "[%(asctime)s] %(message)s"

    FORMATS = {
        logging.DEBUG: bright_magenta + format + reset,
        logging.INFO: bright_green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def logger(error_logs_path: str = 'logs/error_logs',
           all_logs_path: str = 'logs/logs',
           time_based_logs: bool = False):
    # creating custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    # creating handlers
    stream_handler = logging.StreamHandler()
    if time_based_logs:
        error_handler = logging.FileHandler(
            f'error_logs/logs_{datetime.now().strftime("%m-%d-%Y - %H_%M_%S_%f")[:-3]}'
            f'.log')
        file_handler = logging.FileHandler(
            f'logs/logs_{datetime.now().strftime("%m-%d-%Y - %H_%M_%S_%f")[:-3]}.log')
    else:
        makedirs(fr'{get_project_root()}/{error_logs_path}', exist_ok=True)
        error_handler = logging.FileHandler(
            fr'{get_project_root()}/{error_logs_path}/just_errors.log')
        makedirs(fr'{get_project_root()}/{all_logs_path}', exist_ok=True)
        file_handler = logging.FileHandler(fr'{get_project_root()}/{all_logs_path}/all.log')

    stream_handler.setLevel(LOGGING_LEVEL)  # this should be on .INFO level for production
    error_handler.setLevel(logging.ERROR)
    file_handler.setLevel(logging.DEBUG)

    # creating formats and adding it to handlers
    file_format = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s \n\t[%(filename)s:%(lineno)d)]\n"
    )
    stream_handler.setFormatter(CustomFormatter())
    file_handler.setFormatter(file_format)
    error_handler.setFormatter(file_format)

    if not logger.handlers:
        # add handlers to logger
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)

    return logger


if __name__ == "__main__":
    from random import randint
    from asyncio import sleep

    async def one_print(num: int):
        log = Log(f'[{num}]', do_update_title=False)
        for _ in range(2):
            log.debug('Hello.')
            await sleep(randint(1, 3))

    async def multi():
        await asyncio.gather(*(one_print(num) for num in range(10)))

    asyncio.run(multi())
