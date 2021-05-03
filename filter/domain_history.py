import os
import time

import email
import re

import shutil

import logging
from daemonize import Daemonize

## sqlite3
import sqlite3

import datetime

## Handle arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Debug level set from logging.WARNING to logging.DEBUG')
parser.add_argument('-s', '--sleep', type=int, help='Daemon process sleep duration (in seconds) between loops')
args = parser.parse_args()


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.sep)
MAIL_DIR = os.path.join(ROOT_DIR, 'mailu', 'mail')
USER_DIRS = next(os.walk(MAIL_DIR))[1]


## Control which emails (files) to check
CHECK_ALL_EMAILS = True
CHECK_EMAILS_MODIFIED_WITHIN = 20 # Check all emails that are last modified within t seconds
SLEEP_DURATION = args.sleep if args.sleep else 5 # second, default is 5

## Daemonize
pid = "process.pid"
logger = logging.getLogger(__name__)

if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)

logger.propagate = False
fh = logging.FileHandler("process.log", "w")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

def connect_db():
    global conn

    start_time = datetime.datetime.now()
    try:
        conn = sqlite3.connect(os.path.join(THIS_DIR, 'domain.db'))
    except:
        logger.error("I am unable to connect to the database")

    global connect_db_time
    connect_db_time = datetime.datetime.now()
    logger.info(f'Time elapsed for connecting to the database: {datetime.datetime.now() - start_time}')

def modify_userdir(USER_DIR):
    JUNK_DIR = os.path.join(USER_DIR, '.Junk')

    start_time = datetime.datetime.now()

    # conn.execute('''DROP TABLE known_sender;''')

    # conn.execute('''CREATE TABLE IF NOT EXISTS known_sender (address TEXT PRIMARY KEY NOT NULL);''')
    
    address = "\'admin@michaelfong.co\'"
    try:
        conn.execute(f'''INSERT INTO known_sender (address) VALUES ({address});''')
        conn.commit()
    except Exception as e:
        logger.error(f'{e} in SETKNOWN operation for address {address}')
        conn.rollback()

    logger.info(f'Time elapsed for SETKNOWN operation: {datetime.datetime.now() - start_time}')

    _, _, filenames = next(os.walk(os.path.join(USER_DIR, 'cur')))
    logger.info(filenames)

def main():
    connect_db()
    modify_userdir(USER_DIRS[0])
    # cursor = conn.execute('''SELECT * FROM untitled_table_1;''')
    # for row in cursor:
    #     print(row)
    # while True:
    #     logger.info("Fetching Inbox")

    #     with open(os.path.join(THIS_DIR, DOMAIN_FILE), "r") as f:
    #         domain_list = f.read().splitlines()
    #     logger.info(f"Recognized domain list from {DOMAIN_FILE}: {domain_list}")

    #     for filename in os.listdir(INBOX_DIR):
    #         filepath = os.path.join(INBOX_DIR, filename)
    #         mtime = os.stat(filepath).st_mtime

    #         if CHECK_ALL_EMAILS == True or time.time() - mtime < CHECK_EMAILS_MODIFIED_WITHIN: # Check this email (file)

    #             logger.info(f"Checking email {filename}")

    #             with open(filepath, "r") as f:
    #                 msg = email.message_from_file(f) # Whole email message including both headers and content

    #                 parser = email.parser.HeaderParser()
    #                 headers = parser.parsestr(msg.as_string())

    #                 # for h in headers.items(): # Get all header information, this can be commented since we now just need to identify the sender
    #                 #     print(h)

    #                 sender = headers['From']

    #                 ## Add banner to Subject
    #                 subject = headers['Subject']
    #                 if subject.startswith('[FROM NEW SENDER] '):
    #                     pass
    #                 else:
    #                     headers['Subject'] = "[FROM NEW SENDER] " + subject

    #                 m = re.search(r"\<(.*?)\>", sender) # In case sender is something like '"Chan, Tai Man" <ctm@gmail.com>' instead of 'ctm@gmail.com'
    #                 if m != None:
    #                     sender = m.group(1)

    #                 logger.info(f"From: {sender}")

    #                 if sender not in domain_list:
    #                     ## Move the email from Inbox mailbox to New Sender mailbox
    #                     logger.info(f"Sender address not recognized, now move email from {INBOX_MAILBOX} to {NEW_SENDER_MAILBOX}")
    #                     shutil.move(filepath, os.path.join(NEW_SENDER_DIR, filename))
    #                 else:
    #                     logger.info("Sender address recognized")

    #     logger.info(f"Now sleep for {SLEEP_DURATION} seconds")
    #     time.sleep(SLEEP_DURATION)

daemon = Daemonize(app="domain_history", pid=pid, action=main, logger=logger, keep_fds=keep_fds)
daemon.start()


