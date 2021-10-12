from dependency_injector import containers, providers
import os

import sqlite3
from .event import maildir
from .models.user_model import UserFactory
from .models.sender_model import SqliteSenderRepository

import logging

logger = logging.getLogger()


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()
    config.from_yaml("config/eguard-merged.yml")

    #### Export user_dirs ####
    # When only the direct parent `mail_dir` of the users is configured
    if config.path.user_dirs() is None:
        _user_dirs = [f.path for f in os.scandir(config.path.mail_dir()) if f.is_dir()]
    else:
        _user_dirs = config.path.user_dirs()

    user_dirs = providers.Object(_user_dirs)
    #### END ####

    #### User factory and event handler factories for different mail directories ####
    user_factory_singleton = providers.Singleton(UserFactory)
    user_factory = providers.Factory(user_factory_singleton().create_user)

    cur_inbox_event_handler_factory = providers.Factory(
        maildir.CurInboxEventHandler,
    )
    new_inbox_event_handler_factory = providers.Factory(
        maildir.NewInboxEventHandler,
    )
    cur_junk_event_handler_factory = providers.Factory(
        maildir.CurJunkEventHandler,
    )
    new_junk_event_handler_factory = providers.Factory(
        maildir.NewJunkEventHandler,
    )
    #### END ####

    #### Database ####
    sender_repository = providers.Factory(
        SqliteSenderRepository,
    )

    user_dir_event_handler_factory = providers.Factory(
        maildir.UserDirEventHandler,
        sender_repository=sender_repository,
    )

    #### END ####
