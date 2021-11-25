from .util.message_util import find_address_from_message
from .models.sender_repository import SqliteSenderRepository
from .models.user_model import User
import os


class FetchAndBuildHelper:
    def __init__(self, user: User, sender_repository: SqliteSenderRepository):
        self.user = user
        self.sender_repository = sender_repository

    def fetch_and_build_known_list(self):
        filepaths = [f.path for f in os.scandir(self.user.cur_inbox_dir)]

        for filepath in filepaths:
            flags = filepath.split(",")[-1]

            # Find address from the message
            address = find_address_from_message(filepath)

            if "S" in flags:
                self.sender_repository.insert_address_to_known_sender(
                    self.user.email, address
                )

    def fetch_and_build_junk_list(self):
        filepaths = [f.path for f in os.scandir(self.user.cur_junk_dir)]

        for filepath in filepaths:
            address = find_address_from_message(filepath)
            self.sender_repository.insert_address_to_junk_sender(address)
