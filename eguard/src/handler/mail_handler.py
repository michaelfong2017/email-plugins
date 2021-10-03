from watchdog.events import FileSystemEventHandler
import logging

logger = logging.getLogger()

class MailHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        logger.info(event)
        return super().on_any_event(event)