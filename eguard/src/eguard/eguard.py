import typer
from .util.logger import create_logger
from .event.maildir import MaildirEventHandler
from watchdog.observers import Observer
import time
import yaml


def main(
    command: str = typer.Argument(
        ...,
        help="""
        If start:

            Start eguard in a tmux session named 'eguard'.


        If restart:

            Restart eguard in the previous tmux session named 'eguard'.

        If stop:

            Stop eguard in the previous tmux session named 'eguard'.


        """,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Debug level set from logging.ERROR to logging.DEBUG",
    ),
):
    """
    This application supports Linux and MacOS only.
    """

    # Logger
    logger = create_logger(debug=debug)

    # Read config file
    config_file_merged = "config/eguard-merged.yml"
    with open(config_file_merged, "r") as f:
        config = yaml.safe_load(f)
    logger.info(config)

    path = "src/eguard"
    event_handler = MaildirEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
