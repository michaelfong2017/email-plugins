import logging
from datetime import datetime
from pytz import timezone, utc
from functools import wraps
import inspect


def create_logger(debug=False):
    logger = logging.getLogger()

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    if not len(logger.handlers) == 0:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s:%(lineno)s [%(funcName)s] %(message)s"
    )

    logger.addHandler(
        handler("logs/debug.log", level=logging.DEBUG, formatter=formatter)
    )
    logger.addHandler(handler("logs/info.log", level=logging.INFO, formatter=formatter))
    logger.addHandler(
        handler("logs/error.log", level=logging.ERROR, formatter=formatter)
    )

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def handler(
    filepath,
    level=logging.DEBUG,
    formatter=logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
    filemode="w",
):
    fh = logging.FileHandler(filepath, filemode)

    def hong_kong(*args):
        utc_dt = utc.localize(datetime.utcnow())
        my_tz = timezone("Hongkong")
        converted = utc_dt.astimezone(my_tz)
        return converted.timetuple()

    formatter.converter = hong_kong

    fh.setLevel(level)
    fh.setFormatter(formatter)

    return fh


def timing(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        logger = logging.getLogger()
        start = datetime.now()
        result = f(*args, **kwargs)
        end = datetime.now()
        duration = str(end - start)
        f_file = inspect.getmodule(f).__file__
        f_first_lineno = inspect.getsourcelines(f)[-1]
        outer_frameinfo = inspect.getouterframes(inspect.currentframe())[1]
        logger.info(
            f"""Time elapsed for executing the below function is {duration}.
File "{f_file}", {f.__name__}:{f_first_lineno} in
File "{outer_frameinfo.filename}", {outer_frameinfo.function}:{outer_frameinfo.lineno}"""
        )
        return result

    return wrapped


def create_stat_logger():
    logger = logging.getLogger("stat")

    logger.setLevel(logging.DEBUG)

    ## Set logger.propagate to False so that events logged to this logger
    ## will not be passed to the handlers of higher level (ancestor) loggers.
    ## That is, in the current settings, we don't want logging.getLogger()
    ## to receive logs from logging.getLogger("stat").
    logger.propagate = False

    if not len(logger.handlers) == 0:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s:%(lineno)s [%(funcName)s] %(message)s"
    )

    logger.addHandler(
        handler("logs/stat.log", level=logging.INFO, formatter=formatter, filemode="a")
    )

    return logger