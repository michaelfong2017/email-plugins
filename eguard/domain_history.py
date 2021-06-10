# My own utils
from util.message_util import *
from util.database_util import *
from util.logger import *
# Handle arguments
from util.arg_parser import *

import os
import time


import re

from daemonize import Daemonize

# sqlite3
import sqlite3

import datetime


# Read config file
import toml

# Undo queue
from queue import Queue

# Handle arguments from command line
args = parse_args()
SLEEP_DURATION = args.sleep if args.sleep else 1 # second, default is 1
DEBUG = args.debug

# Logger
logger, keep_fds = create_logger(debug=DEBUG)

# Path
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# toml
config = toml.load(os.path.join(THIS_DIR, 'eguard.toml'))

try:
    if 'UserDirectories' in config['Path']:
        USER_DIRS = config['Path']['UserDirectories']
    else:
        MAIL_DIR = config['Path']['MailDir']
        USER_DIRS = [f.path for f in os.scandir(MAIL_DIR) if f.is_dir()]

    INBOX_DIR_FROM_USER_DIR = config['Path']['InboxDirFromUserDir']
    JUNK_DIR_FROM_USER_DIR = config['Path']['JunkDirFromUserDir']

except KeyError as e:
    logger.error(f'{e}\nPlease check that the above key is properly defined in the configuration file.')

logger.info(f'USER_DIRS: {USER_DIRS}')
logger.info(f'INBOX_DIR_FROM_USER_DIR: {INBOX_DIR_FROM_USER_DIR}')
logger.info(f'JUNK_DIR_FROM_USER_DIR: {JUNK_DIR_FROM_USER_DIR}')


# Construct a check set that stores a set of checked mails in a mailbox
# so that mails are not redundantly checked.

# A set that contains all mails in a mailbox should also be constructed 
# to remove mails from the check set when these mails do not exist, 
# so that when the same mail name is reused, the mail can be checked again.
userdir_to_maildir_to_setname_to_set = {}
for userdir in USER_DIRS:
    userdir_to_maildir_to_setname_to_set[userdir] = {}
    for maildir in [INBOX_DIR_FROM_USER_DIR, JUNK_DIR_FROM_USER_DIR]:
        userdir_to_maildir_to_setname_to_set[userdir][maildir] = {}
        for setname in ['checked']:
            userdir_to_maildir_to_setname_to_set[userdir][maildir][setname] = set()

logger.info(f'userdir_to_maildir_to_setname_to_set: {userdir_to_maildir_to_setname_to_set}')


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


def process_userdir(USER_DIR):
    start_time = datetime.datetime.now()

    '''
    INBOX_DIR
    '''
    INBOX_DIR = os.path.join(USER_DIR, INBOX_DIR_FROM_USER_DIR)
    logger.info(f"Entering inbox directory {INBOX_DIR}")

    inbox_all = set([f.name for f in os.scandir(INBOX_DIR)])

    '''Avoid redundant check'''
    # The set of mails that are previously checked.
    inbox_checked = userdir_to_maildir_to_setname_to_set[USER_DIR][INBOX_DIR_FROM_USER_DIR]['checked'] 

    # The set of mails that are previously checked but do not exist in the current mail directory.
    # This means that these mails have been altered, usually the flags are altered.
    inbox_previous = inbox_checked.difference(inbox_all)

    # The set of checked mails must be updated so that these mails exist in the current step.
    # Otherwise, after some user actions and if the mails have the same name again in the future,
    # these mails will not be checked and there will be bugs.
    userdir_to_maildir_to_setname_to_set[USER_DIR][INBOX_DIR_FROM_USER_DIR]['checked'] = inbox_all.intersection(userdir_to_maildir_to_setname_to_set[USER_DIR][INBOX_DIR_FROM_USER_DIR]['checked'])
    inbox_checked = userdir_to_maildir_to_setname_to_set[USER_DIR][INBOX_DIR_FROM_USER_DIR]['checked'] 

    # The set of mails that are not checked previously and are about to be checked.
    inbox_unchecked = inbox_all.difference(inbox_checked)

    logger.info(f'inbox_previous: {inbox_previous}')
    logger.info(f'inbox_unchecked length: {len(inbox_unchecked)}')

    for inbox_mail in inbox_unchecked:
        logger.info(f"Checking email {inbox_mail}")

        filepath = os.path.join(INBOX_DIR, inbox_mail)

        flags = inbox_mail.split(',')[-1]

        # If message is read, mark as recognized in database.
        if ('S' in flags):
            # Remove banner from Subject if exists
            remove_banner_from_subject(filepath)

            # Remove the previously prepended warning banner from mail body (have to handle for both plain and html)
            remove_banner_from_body(filepath)

            # Find address from the message
            address = find_address_from_message(filepath)

            # Insert the address to known sender
            insert_address_to_known_sender(address, conn, logger=logger)

        else:
            # In order to allow the user to unrecognize mistakely recognized sender addresses,
            # we need to find mails that are previously checked and previously marked as seen.
            # Therefore, we need to find the mails in inbox_previous that have the flag 'S' (seen).
            # If the user now marks these mails as unseen from seen, these mails' sender addresses
            # will be changed from recognized to unrecognized.
            will_unrecognize = False
            for mail_previous in inbox_previous:
                previous_flags = mail_previous.split(',')[-1]

                if (inbox_mail.split(',')[0] == mail_previous.split(',')[0] and 'S' in previous_flags):
                    will_unrecognize = True
                    break
            
            if will_unrecognize:
                # Add banner to Subject
                add_banner_to_subject(filepath)

                # Add banner to body
                prepend_banner_to_body(filepath)


                # Find address from the message
                address = find_address_from_message(filepath)

                # Delete the address from known sender
                delete_address_from_known_sender(address, conn, logger=logger)
                
            else:
                # If message is unread, add a warning banner to the subject.
                
                # Find address from the message
                address = find_address_from_message(filepath)
    
                # Add banner to Subject if record does not exist in database
                if not is_address_exists_in_known_sender(address, conn, logger=logger) == True:
                    add_banner_to_subject(filepath)

                    # Add banner to body
                    prepend_banner_to_body(filepath)
                else:
                    pass

    
        # Rename file based on size
        new_filename = rename_file_based_on_size(INBOX_DIR, inbox_mail)
            
        userdir_to_maildir_to_setname_to_set[USER_DIR][INBOX_DIR_FROM_USER_DIR]['checked'].add(new_filename)



    '''
    JUNK_DIR
    '''
    JUNK_DIR = os.path.join(USER_DIR, JUNK_DIR_FROM_USER_DIR)
    logger.info(f"Entering junk directory {JUNK_DIR}")

    junk_all = set([f.name for f in os.scandir(JUNK_DIR)])

    # Avoid redundant check
    userdir_to_maildir_to_setname_to_set[USER_DIR][JUNK_DIR_FROM_USER_DIR]['checked'] = junk_all.intersection(userdir_to_maildir_to_setname_to_set[USER_DIR][JUNK_DIR_FROM_USER_DIR]['checked'])
    junk_checked = userdir_to_maildir_to_setname_to_set[USER_DIR][JUNK_DIR_FROM_USER_DIR]['checked'] 
    junk_unchecked = junk_all.difference(junk_checked)

    logger.info(f'junk_unchecked length: {len(junk_unchecked)}')

    for junk_mail in junk_unchecked:
        logger.info(f"Checking email {junk_mail}")

        filepath = os.path.join(JUNK_DIR, junk_mail)

        # Find address from the message
        address = find_address_from_message(filepath)

        # Delete the address from known sender
        insert_address_to_junk_sender(address, conn, logger=logger)

        userdir_to_maildir_to_setname_to_set[USER_DIR][JUNK_DIR_FROM_USER_DIR]['checked'].add(junk_mail)


    logger.info(f'Time elapsed for processing {USER_DIR}: {datetime.datetime.now() - start_time}')


def main():
    while True:
        try:
            conn.execute(f'SELECT count(*) FROM known_sender')

        except (NameError, sqlite3.ProgrammingError) as e:
            logger.error(f'{e}')
            connect_db()

        try:
            conn.execute(f'SELECT count(*) FROM known_sender')

        except (sqlite3.OperationalError) as e:
            logger.error(f'{e}')
            init_db(conn, logger=logger)

        try:
            process_userdir(USER_DIRS[0])

        finally:
            if conn:
                if datetime.datetime.now() - datetime.timedelta(seconds=1800) > connect_db_time:
                    conn.close()

        logger.info(f"Now sleep for {SLEEP_DURATION} seconds")
        time.sleep(SLEEP_DURATION)


# Daemonize
pid = ".process.pid"

daemon = Daemonize(app="domain_history", pid=pid, action=main, logger=logger, keep_fds=keep_fds)
daemon.start()


