from dependency_injector import containers
import typer

from .util.logger import create_logger
from .containers import Container
from watchdog.observers import Observer
import time

#### Dependency injector: import modules to be wired with the container.
from .event import maildir
from .models import user_model

#### END ####


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

        If fetchandbuild:

            Fetch existing unseen mail list and junk mail list to build
            the known sender list and junk sender list for every user.

        If updatebanners:

            Accomplish two tasks. First, add/remove banners depending on the
            current state of the database storing the known sender list and
            junk sender list. Second, update the wording and appearance of
            existing banners as configured in mutable_email.py. Banners with
            prefix OLD_ will be replaced with banners without prefix OLD_
            correspondingly. This is applied to each email for every user.


        """,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Debug level set from logging.ERROR to logging.DEBUG.",
    ),
    monitor_user_dir: bool = typer.Option(
        False,
        "--monitor-user-dir",
        "-m",
        help="Monitor file system events of each user mail directory.",
    ),
):
    """
    This application supports Linux and MacOS only.
    """

    # Logger
    logger = create_logger(debug=debug)

    # Dependency injector
    container = Container()
    # container.wire should be called here. Calling it inside Container class does not work.
    container.wire(modules=[maildir, user_model])

    if command == "start" or command == "restart":
        observer = Observer()
        for user_dir in container.user_dirs():
            user = container.user_factory(user_dir)
            event_handler = container.cur_inbox_event_handler_factory(user)
            observer.schedule(event_handler, user.cur_inbox_dir, recursive=True)
            event_handler = container.new_inbox_event_handler_factory(user)
            observer.schedule(event_handler, user.new_inbox_dir, recursive=True)
            event_handler = container.cur_junk_event_handler_factory(user)
            observer.schedule(event_handler, user.cur_junk_dir, recursive=True)
            event_handler = container.new_junk_event_handler_factory(user)
            observer.schedule(event_handler, user.new_junk_dir, recursive=True)

            if monitor_user_dir:
                event_handler = container.user_dir_event_handler_factory(user)
                observer.schedule(event_handler, user_dir, recursive=False)

        observer.start()
        try:
            while True:
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()

    elif command == "fetchandbuild":
        for user_dir in container.user_dirs():
            user = container.user_factory(user_dir)
            fetch_and_build_helper = container.fetch_and_build_helper_factory(user)
            fetch_and_build_helper.fetch_and_build_known_list()
            fetch_and_build_helper.fetch_and_build_junk_list()

    elif command == "updatebanners":
        for user_dir in container.user_dirs():
            user = container.user_factory(user_dir)
            update_banners_helper = container.update_banners_helper_factory(user)
            update_banners_helper.update_unknown_banners()
            update_banners_helper.update_junk_banners()
            update_banners_helper.update_no_banners()
