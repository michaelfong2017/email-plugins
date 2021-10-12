"""
For different mail directory structures, different event handler implementations are used.
"""
from watchdog.events import FileSystemEventHandler
import logging

from ..models.sender_model import SqliteSenderRepository
from ..models.user_model import User

logger = logging.getLogger()


class CurInboxEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
        logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)


class NewInboxEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
        logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)


class CurJunkEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
        logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)


class NewJunkEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
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
        # logger.info(f"{self.user.email} ; {self} ; {event}")
        print(self.sender_repository.is_address_exists_in_junk_sender(self.user.email))

        return super().on_any_event(event)
