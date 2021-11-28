from .util.message_util import find_address_from_message
from .models.user_model import User
from .models.sender_repository import SqliteSenderRepository
from .mutable_email import (
    UNKNOWN_SUBJECT_BANNER,
    JUNK_SUBJECT_BANNER,
    UNKNOWN_BANNER_PLAIN_TEXT,
    UNKNOWN_BANNER_HTML,
    JUNK_BANNER_PLAIN_TEXT,
    JUNK_BANNER_HTML,
    MutableEmailFactory,
)
import os


class UpdateBannersHelper:
    def __init__(self, user: User, sender_repository: SqliteSenderRepository):
        self.user = user
        self.sender_repository = sender_repository

    def update_unknown_banners(self):
        filepaths = [f.path for f in os.scandir(self.user.cur_inbox_dir)] + [
            f.path for f in os.scandir(self.user.cur_junk_dir)
        ]

        for filepath in filepaths:
            address = find_address_from_message(filepath)

            if not self.sender_repository.is_address_exists_in_junk_sender(
                address
            ) and not self.sender_repository.is_address_exists_in_known_sender(
                self.user.email, address
            ):
                """
                Remove all previously added banner(s), if exists.
                """
                mutable_email = MutableEmailFactory.create_mutable_email(filepath)
                mutable_email = mutable_email.remove_all_banners()
                """"""
                # Add banner to Subject
                # Add banner to body
                mutable_email = mutable_email.add_subject_banner(UNKNOWN_SUBJECT_BANNER)
                mutable_email = mutable_email.add_banners(
                    UNKNOWN_BANNER_PLAIN_TEXT, UNKNOWN_BANNER_HTML
                )

    def update_junk_banners(self):
        filepaths = [f.path for f in os.scandir(self.user.cur_inbox_dir)] + [
            f.path for f in os.scandir(self.user.cur_junk_dir)
        ]

        for filepath in filepaths:
            address = find_address_from_message(filepath)

            if self.sender_repository.is_address_exists_in_junk_sender(address):
                """
                Remove all previously added banner(s), if exists.
                """
                mutable_email = MutableEmailFactory.create_mutable_email(filepath)
                mutable_email = mutable_email.remove_all_banners()
                """"""
                # Add banner to Subject
                # Add banner to body
                mutable_email = mutable_email.add_subject_banner(JUNK_SUBJECT_BANNER)
                mutable_email = mutable_email.add_banners(
                    JUNK_BANNER_PLAIN_TEXT, JUNK_BANNER_HTML
                )

    def update_no_banners(self):
        filepaths = [f.path for f in os.scandir(self.user.cur_inbox_dir)] + [
            f.path for f in os.scandir(self.user.cur_junk_dir)
        ]

        for filepath in filepaths:
            address = find_address_from_message(filepath)

            if not self.sender_repository.is_address_exists_in_junk_sender(
                address
            ) and self.sender_repository.is_address_exists_in_known_sender(
                self.user.email, address
            ):
                """
                Remove all previously added banner(s), if exists.
                """
                mutable_email = MutableEmailFactory.create_mutable_email(filepath)
                mutable_email = mutable_email.remove_all_banners()
                """"""
