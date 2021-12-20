from dependency_injector import containers
import typer

from .util.logger import create_logger, create_stat_logger
from .containers import Container
from watchdog.observers import Observer
import time
import os

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

            Fetch existing unseen mail directory and junk mail directory of every user
            to build a known sender list for every user and build a common junk
            sender list for all users. This does not remove any existing records in
            the known sender lists and the junk sender list, if exist.

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
    stat_logger = create_stat_logger()

    # Dependency injector
    container = Container()
    # container.wire should be called here. Calling it inside Container class does not work.
    container.wire(modules=[maildir, user_model])

    if command == "start" or command == "restart":
        observer = Observer()
        for user_dir in container.user_dirs():
            user = container.user_factory(user_dir)

            if os.path.isdir(user.cur_inbox_dir):
                event_handler = container.cur_inbox_event_handler_factory(user)
                observer.schedule(event_handler, user.cur_inbox_dir, recursive=True)
            else:
                logger.warning(f"Directory \"{user.cur_inbox_dir}\" does not exist.")

            if os.path.isdir(user.new_inbox_dir):
                event_handler = container.new_inbox_event_handler_factory(user)
                observer.schedule(event_handler, user.new_inbox_dir, recursive=True)
            else:
                logger.warning(f"Directory \"{user.new_inbox_dir}\" does not exist.")

            if os.path.isdir(user.cur_junk_dir):
                event_handler = container.cur_junk_event_handler_factory(user)
                observer.schedule(event_handler, user.cur_junk_dir, recursive=True)
            else:
                logger.warning(f"Directory \"{user.cur_junk_dir}\" does not exist.")

            if os.path.isdir(user.new_junk_dir):
                event_handler = container.new_junk_event_handler_factory(user)
                observer.schedule(event_handler, user.new_junk_dir, recursive=True)
            else:
                logger.warning(f"Directory \"{user.new_junk_dir}\" does not exist.")


            if monitor_user_dir:
                if os.path.isdir(user_dir):
                    event_handler = container.user_dir_event_handler_factory(user)
                    observer.schedule(event_handler, user_dir, recursive=False)
                else:
                    logger.warning(f"Directory \"{user_dir}\" does not exist.")

        observer.start()
        try:
            while True:
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()

    elif command == "fetchandbuild":
        print(container.user_dirs())

        """
        Collect statistics
        """
        repository = container.sender_repository()
        """
        Collect statistics END
        """

        """
        Collect statistics
        """
        old_junk_set = repository.select_addresses_from_junk_sender()
        """
        Collect statistics END
        """

        for user_dir in container.user_dirs():
            user = container.user_factory(user_dir)

            """
            Collect statistics
            """
            old_set = None
            if os.path.isdir(user.cur_inbox_dir) or os.path.isdir(user.cur_junk_dir):
                old_set = repository.select_addresses_from_known_sender(user.email)
            """
            Collect statistics END
            """

            fetch_and_build_helper = container.fetch_and_build_helper_factory(user)
            fetch_and_build_helper.fetch_and_build_known_list()
            fetch_and_build_helper.fetch_and_build_junk_list()

            """
            Collect statistics
            """
            new_set = None
            if os.path.isdir(user.cur_inbox_dir) or os.path.isdir(user.cur_junk_dir):
                new_set = repository.select_addresses_from_known_sender(user.email)

            # stat_logger.info(f"old_set: {old_set}")
            # stat_logger.info(f"new_set: {new_set}")
            if old_set is not None and new_set is not None:
                diff_set = new_set - old_set
                stat_logger.info(f"User {user.email}'s known sender list received {len(diff_set)} insertion(s) after fetchandbuild command.")
            """
            Collect statistics END
            """

        """
        Collect statistics
        """
        new_junk_set = repository.select_addresses_from_junk_sender()
        diff_junk_set = new_junk_set - old_junk_set
        stat_logger.info(f"Junk sender list received {len(diff_junk_set)} insertion(s) after fetchandbuild command.")
        """
        Collect statistics END
        """

    elif command == "updatebanners":
        for user_dir in container.user_dirs():
            user = container.user_factory(user_dir)

            if os.path.isdir(user.cur_inbox_dir) and os.path.isdir(user.cur_junk_dir):
                update_banners_helper = container.update_banners_helper_factory(user)
                update_banners_helper.update_unknown_banners()
                update_banners_helper.update_junk_banners()
                update_banners_helper.update_no_banners()

                stat_logger.info(f"updatebanners command is complete for user {user.email}.")
            else:
                logger.warning(f"At least one of the directories \"{user.cur_inbox_dir}\" and \"{user.cur_junk_dir}\" does not exist. Ignore user \"{user.email}\" during {command}.")
