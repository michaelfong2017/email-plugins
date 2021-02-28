import os
import time

import email

from daemonize import Daemonize

USER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX_DIR = os.path.join(USER_DIR, 'cur')
INBOX_MAILBOX = '.INBOX'
NEW_SENDER_MAILBOX = '.INBOX.New Sender'
NEW_SENDER_DIR = os.path.join(USER_DIR, NEW_SENDER_MAILBOX, 'cur')
DOMAIN_FILE = "domain.txt"

## Control which emails (files) to check
CHECK_ALL_EMAILS = True
CHECK_EMAILS_MODIFIED_WITHIN = 20 # Check all emails that are last modified within t seconds

with open(DOMAIN_FILE, "r") as f:
    domain_list = f.readlines()
print(f"Recognized domain list from {DOMAIN_FILE}: {domain_list}")

for filename in os.listdir(INBOX_DIR):
    filepath = os.path.join(INBOX_DIR, filename)
    mtime = os.stat(filepath).st_mtime

    if CHECK_ALL_EMAILS == True or time.time() - mtime < CHECK_EMAILS_MODIFIED_WITHIN: # Check this email (file)

        print(f"Checking email {filename}")

        with open(filepath, "r") as f:
            msg = email.message_from_file(f) # Whole email message including both headers and content

            parser = email.parser.HeaderParser()
            headers = parser.parsestr(msg.as_string())

            # for h in headers.items(): # Get all header information, this can be commented since we now just need to identify the sender
            #     print(h)

            sender = headers['From']

            print(f"From: {sender}")

            if sender not in domain_list:
                # Move the email from Inbox mailbox to New Sender mailbox
                print(f"Sender address not recognized, now moving email from {INBOX_MAILBOX} to {NEW_SENDER_MAILBOX}")