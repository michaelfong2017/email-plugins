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
import threading

logger = logging.getLogger()


"""
CurInboxEventHandler exists to monitor the current inbox mail directory to notify
and handle any case when the user marks a mail as read/unread.
It is important to explicitly exclude any other cases.

Exclude case 1: adding/removing junk warning banner or caution banner results in
a FileMovedEvent, as user action "mark as read" or "mark as unread" does.
Exclude case 2: clicking the junk folder icon triggers FileMovedEvent by adding a
"a" flag to the filename; or, renaming to remove the flag "a" before moving the
mail to the junk folder.

The way to differentiate between these two types of FileMovedEvent is to compare
the src_path filename and dest_path filename to see whether only the flag "S" 
has been added/removed. For targeted user actions "mark as read" and "mark as unread",
only the flag "S" has been added/removed. On the other hand, for FileMovedEvent fired
by other actions, either the size of the file has changed or other flags like "a"
has been added/removed.

"""


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

        #### Exclude non-targeted FileMovedEvent here.
        ## Exclude case 1
        if "".join(event.src_path.split(",")[:-1]) != "".join(
            event.dest_path.split(",")[:-1]
        ):
            logger.debug("CurInboxEventHandler catches exclude case 1")
            return super().on_any_event(event)

        ## Exclude case 2
        src_flag = set(event.src_path.split(",")[-1])
        dest_flag = set(event.dest_path.split(",")[-1])

        if (src_flag - dest_flag == set("a") and dest_flag - src_flag == set()) or (
            dest_flag - src_flag == set("a") and src_flag - dest_flag == set()
        ):
            logger.debug("CurInboxEventHandler catches exclude case 2")
            return super().on_any_event(event)

        #### END ####

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
            Remove all previously added banner(s), if exists.
            """
            remove_all_banners(filepath)
            """"""

            # Insert the address to junk sender
            self.sender_repository.insert_address_to_junk_sender(address)

            add_banner_to_subject(filepath, is_junk=True)

            add_banner_to_body(filepath, is_junk=True)

            # Rename file based on size
            new_filename = rename_file_based_on_size(self.user.cur_inbox_dir, filename)

            # Move junk mail to junk folder
            move_to_folder(
                self.user.cur_inbox_dir,
                self.user.cur_junk_dir,
                new_filename,
                is_junk=True,
            )

        else:
            # If message is read ('S' for 'seen'), mark as recognized in database.
            if "S" in flags:
                def recognize_later():
                    if os.path.exists(filepath):
                        """
                        Remove all previously added banner(s), if exists.
                        """
                        remove_all_banners(filepath)
                        """"""
                        # Insert the address to known sender
                        self.sender_repository.insert_address_to_known_sender(
                            self.user.email, address
                        )

                        # Rename file based on size
                        rename_file_based_on_size(self.user.cur_inbox_dir, filename)

                t = threading.Timer(10.0, recognize_later)
                # I tested that the thread will no longer be running after the scheduled
                # function is run.
                t.start()
            
            # If the user now marks these mails as unseen from seen, these mails' sender addresses
            # will be changed from recognized to unrecognized.
            else:
                """
                Remove all previously added banner(s), if exists.
                """
                remove_all_banners(filepath)
                """"""

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


"""
NewInboxEventHandler exists to monitor the new inbox mail directory to notify
and handle any case when a new mail from the outside has arrived.

If the new mail sender is in the list of junk sender (for all users) in the database,
    add junk warning banner to and move the mail to the current junk folder.

If the new mail sender is not in the list of junk sender, and is not
in the list of known sender (for that particular user),
    add caution banner to and let the mail enter the current inbox folder
    as usual.

If the new mail sender is not in the list of junk sender, and is in
the list of known sender (for that particular user),
    do not add any banner to and let the mail enter the current inbox
    folder as usual.
"""


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
                Remove all previously added banner(s), if exists.
                """
                remove_all_banners(filepath)
                """"""

                add_banner_to_subject(filepath, is_junk=True)

                add_banner_to_body(filepath, is_junk=True)

                # For new mail only, append :2,
                new_filename = rename_new_mail_based_on_size(
                    self.user.new_inbox_dir, filename
                )

                # Move junk mail to junk folder
                move_to_folder(
                    self.user.new_inbox_dir,
                    self.user.cur_junk_dir,
                    new_filename,
                    is_junk=True,
                )

            # If the sender address is not in the junk list, check if it is in the known sender list
            else:
                """
                Remove all previously added banner(s), if exists.
                """
                remove_all_banners(filepath)
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

                # Rename new mail based on size
                rename_new_mail_based_on_size(self.user.new_inbox_dir, filename)

        return super().on_any_event(event)


"""
CurJunkEventHandler exists to monitor the current junk mail directory to notify
and handle any case when a mail is marked as junk.

For Roundcube, there are 3 ways for users to mark a mail as junk.

(a) Roundcube click the junk folder icon
    -> ... -> <FileCreatedEvent> -> ... -> <FileMovedEvent> ; 
    <FileCreatedEvent> with filename = event.dest_path plus an 'a' flag,
    <FileMovedEvent> with filename = event.dest_path, which is without 'a' flag,
    
  'a' means that the mail is flagged as $Junk and Roundcube uses this
   automatically for marking spam.
   Here, only <FileMovedEvent> is handled.
   <FileCreatedEvent> is the explicitly excluded case.

   The reason for considering dest_path and "without 'a' flag" is that
   this 'a' flag is removed by some means after the mail indeed enters 
   the junk folder. Therefore, it is the last step before we can
   process the mail safely.

(b) Roundcube drag mail to junk folder.
(c) Roundcube More -> Move to -> Junk.
  -> <FileCreatedEvent> ; filename = event.src_path

  or

  -> ... -> <FileCreatedEvent> -> ... -> <FileMovedEvent>, all details as in (a),
  when the filename already has an 'a' flag.
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

        ####
        # Whenever a FileMovedEvent happens,
        # the mail from dest_path is treated as a junk mail.
        ####
        if isinstance(event, FileMovedEvent):
            logger.info(f"{self.user.email} ; {self} ; {event}")

            filepath = event.dest_path
            filename = ntpath.basename(filepath)

            # Find address from the message
            address = find_address_from_message(filepath)

            # Insert the address to junk sender
            self.sender_repository.insert_address_to_junk_sender(address)

            """
            Remove all previously added banner(s), if exists.
            """
            remove_all_banners(filepath)
            """"""

            add_banner_to_subject(filepath, is_junk=True)

            add_banner_to_body(filepath, is_junk=True)

            # Rename file based on size
            rename_file_based_on_size(self.user.cur_junk_dir, filename)

        elif isinstance(event, FileCreatedEvent):
            logger.info(f"{self.user.email} ; {self} ; {event}")

            filepath = event.src_path
            filename = ntpath.basename(filepath)

            flags = filename.split(",")[-1]

            ####
            # Ensure that <FileCreatedEvent> in the case
            # -> ... -> <FileCreatedEvent> -> ... -> <FileMovedEvent>
            # is excluded.
            ####
            if "a" not in flags:
                # Find address from the message
                address = find_address_from_message(filepath)

                # Insert the address to junk sender
                self.sender_repository.insert_address_to_junk_sender(address)

                """
                Remove all previously added banner(s), if exists.
                """
                remove_all_banners(filepath)
                """"""

                add_banner_to_subject(filepath, is_junk=True)

                add_banner_to_body(filepath, is_junk=True)

                # Rename file based on size
                rename_file_based_on_size(self.user.cur_junk_dir, filename)

            ## Exclude case
            else:
                logger.debug("CurJunkEventHandler catches exclude case")

        return super().on_any_event(event)


"""
When a Roundcube user mass drags mails including new mails.
Those new mails will go to the new junk mail directory (the old mails
still go to the current junk mail directory).

These new mails from the new junk mail directory will be directly 
renamed and moved back to the current junk mail directory.
"""


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

        if not isinstance(event, FileCreatedEvent):
            return super().on_any_event(event)

        logger.info(f"{self.user.email} ; {self} ; {event}")

        if event.event_type == "created":
            filepath = event.src_path
            filename = ntpath.basename(filepath)

            """
            Remove all previously added banner(s), if exists.
            """
            remove_all_banners(filepath)
            """"""

            add_banner_to_subject(filepath, is_junk=True)

            add_banner_to_body(filepath, is_junk=True)

            # For new mail only, append :2,
            new_filename = rename_new_mail_based_on_size(
                self.user.new_junk_dir, filename
            )

            # Move junk mail to junk folder
            move_to_folder(
                self.user.new_junk_dir,
                self.user.cur_junk_dir,
                new_filename,
                is_junk=True,
            )

        return super().on_any_event(event)


"""
Just for observing file changes of the user directory when main 
program flag "--monitor-user-dir" or "-m" is passed. The changes
in this directory are not well understood. It is probably only related
to user inbox folder. Codes for observing changes related to other
mail folders have not been implemented yet.
"""


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
