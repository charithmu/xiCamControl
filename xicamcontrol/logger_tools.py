import logging
from colorlog import ColoredFormatter


def get_logger(name):
    # Custom formatter
    formatter = ColoredFormatter(
        "[%(asctime)s] %(log_color)s%(levelname)-8s - %(module)s:%(funcName)s:%(lineno)d - %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )

    log_level = logging.DEBUG
    # create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(console_handler)

    return logger
