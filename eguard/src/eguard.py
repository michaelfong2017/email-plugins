from util.arg_parser import argparse
from util.logger import create_logger

import sys
import time

# Handle arguments
from util.arg_parser import *

from watchdog.observers import Observer

from handler.mail_handler import MailHandler


if __name__ == "__main__":
    # Handle arguments from command line
    args = parse_args()
    SLEEP_DURATION = args.sleep if args.sleep else 1 # second, default is 1
    DEBUG = args.debug

    # Logger
    logger = create_logger(debug=DEBUG)

    path = 'src'
    event_handler = MailHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()