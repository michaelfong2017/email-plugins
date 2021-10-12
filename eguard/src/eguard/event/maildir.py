"""
For different mail directory structures, different event handler implementations are used.
"""
from watchdog.events import (
    DirModifiedEvent,
    FileCreatedEvent,
    FileMovedEvent,
    FileSystemEventHandler,
)
import logging

from ..models.sender_repository import SqliteSenderRepository
from ..models.user_model import User
from ..models.sender_repository import *
from ..util.message_util import *
import ntpath

logger = logging.getLogger()


class CurInboxEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        user: User,
        sender_repository: SqliteSenderRepository,
    ):
        self.user = user
        self.sender_repository = sender_repository

    def on_any_event(self, event):
        logger.debug(f"{self.user.email} ; {self} ; {event}")

        if not isinstance(event, FileMovedEvent):
            return super().on_any_event(event)

        logger.info(f"{self.user.email} ; {self} ; {event}")

        filepath = event.dest_path
        filename = ntpath.basename(filepath)

        flags = filename.split(",")[-1]

        # Find address from the message
        address = find_address_from_message(filepath)

        ####
        # In case of junk mail
        ####
        if self.sender_repository.is_address_exists_in_junk_sender(address):
            """
            Remove previously added unknown subject and unknown banner, if exist.
            """
            remove_banner_from_subject(filepath, is_junk=False)

            remove_banner_from_body(filepath, is_junk=False)
            """"""

            # Insert the address to junk sender
            self.sender_repository.insert_address_to_junk_sender(address)

            add_banner_to_subject(filepath, is_junk=True)

            add_banner_to_body(filepath, is_junk=True)

            # Rename file based on size
            new_filename = rename_file_based_on_size(self.user.cur_inbox_dir, filename)

            # Move junk mail to junk folder
            move_to_junk_folder(
                self.user.cur_inbox_dir, self.user.cur_junk_dir, new_filename
            )

        else:
            """
            Remove previously added junk subject and junk banner, if exist.
            """
            remove_banner_from_subject(filepath, is_junk=True)

            remove_banner_from_body(filepath, is_junk=True)
            """"""

            # If message is read ('S' for 'seen'), mark as recognized in database.
            if "S" in flags:
                """
                Remove previously added unknown subject and unknown banner, if exist.
                """
                remove_banner_from_subject(filepath, is_junk=False)

                remove_banner_from_body(filepath, is_junk=False)
                """"""

                # Insert the address to known sender
                self.sender_repository.insert_address_to_known_sender(
                    self.user.email, address
                )

                # Rename file based on size
                rename_file_based_on_size(self.user.cur_inbox_dir, filename)

            # If the user now marks these mails as unseen from seen, these mails' sender addresses
            # will be changed from recognized to unrecognized.
            else:
                # Add banner to Subject
                add_banner_to_subject(filepath, is_junk=False)

                # Add banner to body
                add_banner_to_body(filepath, is_junk=False)

                # Delete the address from known sender
                self.sender_repository.delete_address_from_known_sender(
                    self.user.email, address
                )

                # Rename file based on size
                rename_file_based_on_size(self.user.cur_inbox_dir, filename)

        return super().on_any_event(event)


class NewInboxEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        user: User,
        sender_repository: SqliteSenderRepository,
    ):
        self.user = user
        self.sender_repository = sender_repository

    def on_any_event(self, event):
        logger.debug(f"{self.user.email} ; {self} ; {event}")

        if not isinstance(event, FileCreatedEvent):
            return super().on_any_event(event)

        logger.info(f"{self.user.email} ; {self} ; {event}")

        if event.event_type == "created":
            filepath = event.src_path
            filename = ntpath.basename(filepath)

            # Find address from the message
            address = find_address_from_message(filepath)

            # If the sender address of the message is in the junk sender list,
            # always add the junk warning banner.
            if self.sender_repository.is_address_exists_in_junk_sender(address):
                """
                Remove previously added unknown subject and unknown banner, if exist.
                """
                remove_banner_from_subject(filepath, is_junk=False)

                remove_banner_from_body(filepath, is_junk=False)
                """"""

                add_banner_to_subject(filepath, is_junk=True)

                add_banner_to_body(filepath, is_junk=True)

                # Rename file based on size
                new_filename = rename_file_based_on_size(
                    self.user.new_inbox_dir, filename
                )

                # Move junk mail to junk folder
                move_to_junk_folder(
                    self.user.new_inbox_dir, self.user.cur_junk_dir, new_filename
                )

            # If the sender address is not in the junk list, check if it is in the known sender list
            else:
                """
                Remove previously added junk subject and junk banner, if exist.
                """
                remove_banner_from_subject(filepath, is_junk=True)

                remove_banner_from_body(filepath, is_junk=True)
                """"""

                # Add banner to Subject if record does not exist in database
                if (
                    not self.sender_repository.is_address_exists_in_known_sender(
                        self.user.email, address
                    )
                    == True
                ):
                    add_banner_to_subject(filepath)

                    # Add banner to body
                    add_banner_to_body(filepath, is_junk=False)

                    # Rename file based on size
                    rename_file_based_on_size(self.user.new_inbox_dir, filename)

        return super().on_any_event(event)


"""
For Roundcube, there are 3 ways for users to mark a mail as junk.

(a) Roundcube click the junk folder icon
  -> ... -> <FileMovedEvent> ; filename = event.dest_path, without 'a' flag, 
  'a' means that the mail is flagged as $Junk and Roundcube uses this
   automatically for marking spam.

   The reason for considering dest_path and "without 'a' flag" is that
   this 'a' flag is removed by some means after the mail indeed enters 
   the junk folder.

(b) Roundcube drag mail to junk folder.
(c) Roundcube More -> Move to -> Junk.
  -> <FileCreatedEvent> ; filename = event.src_path

"""


class CurJunkEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        user: User,
        sender_repository: SqliteSenderRepository,
    ):
        self.user = user
        self.sender_repository = sender_repository

    def on_any_event(self, event):
        logger.debug(f"{self.user.email} ; {self} ; {event}")

        if isinstance(event, FileMovedEvent):
            logger.info(f"{self.user.email} ; {self} ; {event}")

            filepath = event.dest_path
            filename = ntpath.basename(filepath)

            flags = filename.split(",")[-1]

            if "a" not in flags:
                ####
                # In case of junk mail
                ####

                # Find address from the message
                address = find_address_from_message(filepath)

                # Insert the address to junk sender
                self.sender_repository.insert_address_to_junk_sender(address)

                add_banner_to_subject(filepath, is_junk=True)

                add_banner_to_body(filepath, is_junk=True)

                # Rename file based on size
                rename_file_based_on_size(self.user.cur_junk_dir, filename)

        ####
        # In case of junk mail
        ####
        elif isinstance(event, FileCreatedEvent):
            logger.info(f"{self.user.email} ; {self} ; {event}")

            filepath = event.src_path
            filename = ntpath.basename(filepath)

            # Find address from the message
            address = find_address_from_message(filepath)

            # Insert the address to junk sender
            self.sender_repository.insert_address_to_junk_sender(address)

            add_banner_to_subject(filepath, is_junk=True)

            add_banner_to_body(filepath, is_junk=True)

            # Rename file based on size
            rename_file_based_on_size(self.user.cur_junk_dir, filename)

        return super().on_any_event(event)


class NewJunkEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        user: User,
        sender_repository: SqliteSenderRepository,
    ):
        self.user = user
        self.sender_repository = sender_repository

    def on_any_event(self, event):
        logger.debug(f"{self.user.email} ; {self} ; {event}")

        if not isinstance(event, DirModifiedEvent):
            logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)


class UserDirEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        user: User,
        sender_repository: SqliteSenderRepository,
    ):
        self.user = user
        self.sender_repository = sender_repository

    def on_any_event(self, event):
        logger.debug(f"{self.user.email} ; {self} ; {event}")

        if not isinstance(event, DirModifiedEvent):
            logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)
