import logging
from datetime import datetime
from pytz import timezone, utc

def create_logger(debug=False):
    logger = logging.getLogger()

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)

    if not len(logger.handlers) == 0:
        logger.handlers.clear()

    fh = logging.FileHandler("logs/output.log", "w")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    def hong_kong(*args):
        utc_dt = utc.localize(datetime.utcnow())
        my_tz = timezone("Hongkong")
        converted = utc_dt.astimezone(my_tz)
        return converted.timetuple()

    formatter.converter = hong_kong

    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
