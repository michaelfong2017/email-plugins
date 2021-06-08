import logging

def create_logger(debug=False):
    logger = logging.getLogger(__name__)

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.CRITICAL)

    if not len(logger.handlers) == 0:
        logger.handlers.clear()

    fh = logging.FileHandler("process.log", "w")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    keep_fds = [fh.stream.fileno()] # This line is needed only for daemonize

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger, keep_fds