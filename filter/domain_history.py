import os
import time

import email
import re

import shutil

import logging
from daemonize import Daemonize

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX_DIR = os.path.join(USER_DIR, 'cur')
INBOX_MAILBOX = '.INBOX'
NEW_SENDER_MAILBOX = '.INBOX.New Sender'
NEW_SENDER_DIR = os.path.join(USER_DIR, NEW_SENDER_MAILBOX, 'cur')
DOMAIN_FILE = "domain.txt"

## Control which emails (files) to check
CHECK_ALL_EMAILS = True
CHECK_EMAILS_MODIFIED_WITHIN = 20 # Check all emails that are last modified within t seconds
SLEEP_DURATION = 10 # second

## Daemonize
pid = "process.pid"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler("process.log", "w")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

def main():
    while True:
        logger.info("Fetching Inbox")

        with open(os.path.join(THIS_DIR, DOMAIN_FILE), "r") as f:
            domain_list = f.read().splitlines()
        logger.info(f"Recognized domain list from {DOMAIN_FILE}: {domain_list}")

        for filename in os.listdir(INBOX_DIR):
            filepath = os.path.join(INBOX_DIR, filename)
            mtime = os.stat(filepath).st_mtime

            if CHECK_ALL_EMAILS == True or time.time() - mtime < CHECK_EMAILS_MODIFIED_WITHIN: # Check this email (file)

                logger.info(f"Checking email {filename}")

                with open(filepath, "r") as f:
                    msg = email.message_from_file(f) # Whole email message including both headers and content

                    parser = email.parser.HeaderParser()
                    headers = parser.parsestr(msg.as_string())

                    # for h in headers.items(): # Get all header information, this can be commented since we now just need to identify the sender
                    #     print(h)

                    sender = headers['From']

                    m = re.search(r"\<(.*?)\>", sender) # In case sender is something like '"Chan, Tai Man" <ctm@gmail.com>' instead of 'ctm@gmail.com'
                    if m != None:
                        sender = m.group(1)

                    logger.info(f"From: {sender}")

                    if sender not in domain_list:
                        # Move the email from Inbox mailbox to New Sender mailbox
                        print(f"Sender address not recognized, now move email from {INBOX_MAILBOX} to {NEW_SENDER_MAILBOX}")
                        shutil.move(filepath, os.path.join(NEW_SENDER_DIR, filename))
                    else:
                        logger.info("Sender address recognized")

        logger.info(f"Now sleep for {SLEEP_DURATION} seconds")
        time.sleep(SLEEP_DURATION)

daemon = Daemonize(app="domain_history", pid=pid, action=main, logger=logger, keep_fds=keep_fds)
daemon.start()


