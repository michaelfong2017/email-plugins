import os
import time

import email

from daemonize import Daemonize

USER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX_DIR = os.path.join(USER_DIR, 'cur')
NEW_USER_DIR = os.path.join(USER_DIR, '.INBOX.New Sender', 'cur')

## Control which emails (files) to check
CHECK_ALL_EMAILS = True
CHECK_EMAILS_MODIFIED_WITHIN = 20 # Check all emails that are last modified within t seconds

for filename in os.listdir(INBOX_DIR):
    filepath = os.path.join(INBOX_DIR, filename)
    mtime = os.stat(filepath).st_mtime

    if CHECK_ALL_EMAILS == True or time.time() - mtime < CHECK_EMAILS_MODIFIED_WITHIN: # Check this email (file)

        with open(filepath, "r") as f:
            msg = email.message_from_file(f)
            print(msg)

            parser = email.parser.HeaderParser()
            headers = parser.parsestr(msg.as_string())

            for h in headers.items():
                print h