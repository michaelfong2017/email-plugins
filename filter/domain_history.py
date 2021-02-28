import os

from time import sleep
from daemonize import Daemonize

USER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX_DIR = os.path.join(USER_DIR, 'cur')
NEW_USER_DIR = os.path.join(USER_DIR, '.INBOX.New Sender', 'cur')

for filename in os.listdir(INBOX_DIR):
    filename = "'" + filename + "'"
    print(filename)
    print(os.stat(filename).st_mtime)
