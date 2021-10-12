from dependency_injector import containers, providers
import os

from .event import maildir
from .models.user_model import UserFactory
from .models.sender_repository import SqliteSenderRepository

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
    ## Database ##
    sender_repository = providers.Factory(
        SqliteSenderRepository,
    )
    ## END ##

    user_factory_singleton = providers.Singleton(UserFactory)
    user_factory = providers.Factory(user_factory_singleton().create_user)

    cur_inbox_event_handler_factory = providers.Factory(
        maildir.CurInboxEventHandler,
        sender_repository=sender_repository,
    )
    new_inbox_event_handler_factory = providers.Factory(
        maildir.NewInboxEventHandler,
        sender_repository=sender_repository,
    )
    cur_junk_event_handler_factory = providers.Factory(
        maildir.CurJunkEventHandler,
        sender_repository=sender_repository,
    )
    new_junk_event_handler_factory = providers.Factory(
        maildir.NewJunkEventHandler,
        sender_repository=sender_repository,
    )
    user_dir_event_handler_factory = providers.Factory(
        maildir.UserDirEventHandler,
        sender_repository=sender_repository,
    )
    #### END ####
