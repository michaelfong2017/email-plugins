import typer
from src.eguard.containers import Container
from watchdog.observers import Observer
import time

#### Dependency injector: import modules to be wired with the container.
from src.eguard.event import maildir
from src.eguard.models import user_model

#### END ####

import logging

logger = logging.getLogger()

def test_create_users():
    logger.info('hi')
    assert True is True