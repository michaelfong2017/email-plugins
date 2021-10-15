from dataclasses import dataclass
from dependency_injector.wiring import Provide
import ntpath
import os


@dataclass
class User:
    email: str
    cur_inbox_dir: str
    new_inbox_dir: str
    cur_junk_dir: str
    new_junk_dir: str


class UserFactory:
    domain = Provide["config.domain"]
    cur_inbox_dir_from_user_dir = Provide["config.path.cur_inbox_dir_from_user_dir"]
    new_inbox_dir_from_user_dir = Provide["config.path.new_inbox_dir_from_user_dir"]
    cur_junk_dir_from_user_dir = Provide["config.path.cur_junk_dir_from_user_dir"]
    new_junk_dir_from_user_dir = Provide["config.path.new_junk_dir_from_user_dir"]

    def create_user(self, user_dir: str):
        email = ntpath.basename(user_dir.rstrip("/"))
        if "@" not in email:
            email += "@" + self.domain
        return User(
            email,
            os.path.join(user_dir, self.cur_inbox_dir_from_user_dir),
            os.path.join(user_dir, self.new_inbox_dir_from_user_dir),
            os.path.join(user_dir, self.cur_junk_dir_from_user_dir),
            os.path.join(user_dir, self.new_junk_dir_from_user_dir),
        )
