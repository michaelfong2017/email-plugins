"""
For different mail directory structures, different event handler implementations are used.
"""
from watchdog.events import FileSystemEventHandler
import logging
from ..models.user_model import User

_logger = logging.getLogger()


class CurInboxEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
        _logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)

class NewInboxEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
        _logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)

class CurJunkEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
        _logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)
        
class NewJunkEventHandler(FileSystemEventHandler):
    def __init__(self, user: User):
        self.user = user

    def on_any_event(self, event):
        _logger.info(f"{self.user.email} ; {self} ; {event}")
        return super().on_any_event(event)