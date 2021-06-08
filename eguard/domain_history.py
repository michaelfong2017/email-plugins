# My own utils
from util.message_util import *
from util.database_util import *
from util.logger import *
# Handle arguments
from util.arg_parser import *

import os
import time

import email
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
SLEEP_DURATION = args.sleep if args.sleep else 1 # second, default is 5
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


# Construct an undo queue in order to unrecognize mistakely recognized sender addresses.
undo_q = Queue(maxsize = 30)


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

def init_db():
    start_time = datetime.datetime.now()
    # conn.execute('''CREATE TABLE IF NOT EXISTS user_pc (id INT PRIMARY KEY NOT NULL, known_address TEXT NOT NULL, junk_address TEXT NOT NULL);''')
    conn.execute('''CREATE TABLE IF NOT EXISTS known_sender (address TEXT PRIMARY KEY NOT NULL);''')
    conn.commit()
    logger.info(f'Time elapsed for initializing the database: {datetime.datetime.now() - start_time}')

def process_userdir(USER_DIR):
    start_time = datetime.datetime.now()

    '''
    INBOX_DIR
    '''
    INBOX_DIR = os.path.join(USER_DIR, INBOX_DIR_FROM_USER_DIR)
    logger.info(f"Entering inbox directory {INBOX_DIR}")

    inbox_mails = [f.name for f in os.scandir(INBOX_DIR)]

    for inbox_mail in inbox_mails:
        logger.info(f"Checking email {inbox_mail}")

        filepath = os.path.join(INBOX_DIR, inbox_mail)

        flags = inbox_mail.split(',')[-1]

        # If message is read, mark as recognized in database.
        if ('S' in flags):
            msg = ""
            headers = ""
            with open(filepath, "r+") as f:
                modified = False

                # Get msg and headers from file for further processing
                msg = email.message_from_file(f) # Whole email message including both headers and content
                parser = email.parser.HeaderParser()
                headers = parser.parsestr(msg.as_string())

                body_plain, body_html = find_body_plain_and_html_from_message(msg)
                
                logger.info('yoyoyoyo')
                logger.info(body_plain)
                logger.info(body_html)

                # modified: Add to an undo queue in order to unrecognize mistakely recognized sender addresses.
                modified = remove_banner_from_subject(msg, f, headers=headers)


            # Find address from the message
            address = find_address_from_message(msg, headers=headers)

            # Insert the address to known sender
            insert_address_to_known_sender(address, conn, logger=logger)

            # Rename file based on size
            new_filename = rename_file_based_on_size(INBOX_DIR, inbox_mail)

            # Add to an undo queue in order to unrecognize mistakely recognized sender addresses.
            if modified:
                undo_q.put(new_filename.split(',')[0])

        else:
            # If message is inside the undo queue, that is, if message is read before but the
            # user decides to unrecognize the message and therefore marks the message as unread.
            if inbox_mail.split(',')[0] in undo_q.queue:
                msg = ""
                headers = ""
                with open(filepath, "r+") as f:
                    # Get msg and headers from file for further processing
                    msg = email.message_from_file(f) # Whole email message including both headers and content
                    parser = email.parser.HeaderParser()
                    headers = parser.parsestr(msg.as_string())

                    # Add banner to Subject
                    add_banner_to_subject(msg, f, headers)

                # Find address from the message
                address = find_address_from_message(msg, headers=headers)

                # Delete the address from known sender
                delete_address_from_known_sender(address, conn, logger=logger)
                
                # Rename file based on size
                rename_file_based_on_size(INBOX_DIR, inbox_mail)


            else:
                # If message is unread, add a warning banner to the subject.
                msg = ""
                headers = ""
                with open(filepath, "r+") as f:
                    # Get msg and headers from file for further processing
                    msg = email.message_from_file(f) # Whole email message including both headers and content
                    parser = email.parser.HeaderParser()
                    headers = parser.parsestr(msg.as_string())
    
                    # Find address from the message
                    address = find_address_from_message(msg, headers=headers)
    
                    # Add banner to Subject if record does not exist in database
                    if is_address_exists_in_known_sender() == True:
                        subject = headers['Subject']
                        if subject.startswith('[FROM NEW SENDER] '):
                            pass
                        else:
                            headers.replace_header('Subject', "[FROM NEW SENDER] " + subject)
                            
                            logger.error(headers)
                            logger.error(headers.as_string())
                            logger.error(headers.__str__())
                            
                            f.seek(0)
                            f.write(headers.as_string())
                            f.truncate()
                    else:
                        pass
    
    
                # Rename file
                new_file_size = os.stat(filepath).st_size
    
                new_filename = re.sub(r',S=[0-9]*,', f',S={new_file_size},', inbox_mail)
    
                os.rename(filepath, os.path.join(INBOX_DIR, new_filename))
            


    '''
    JUNK_DIR
    '''
    JUNK_DIR = os.path.join(USER_DIR, JUNK_DIR_FROM_USER_DIR)
    logger.info(f"Entering junk directory {JUNK_DIR}")

    junk_mails = [f.name for f in os.scandir(JUNK_DIR)]

    for junk_mail in junk_mails:
        logger.info(f"Checking email {junk_mail}")

        filepath = os.path.join(JUNK_DIR, junk_mail)

        with open(filepath, "r") as f:
            msg = email.message_from_file(f) # Whole email message including both headers and content

            parser = email.parser.HeaderParser()
            headers = parser.parsestr(msg.as_string())

            # Find address from the message
            sender = headers['From']

            m = re.search(r"\<(.*?)\>", sender) # In case sender is something like '"Chan, Tai Man" <ctm@gmail.com>' instead of 'ctm@gmail.com'
            if m != None:
                sender = m.group(1)

            logger.info(f"Sender of this email: {sender}")

            # Delete the address from database
            try:
                conn.execute(f'DELETE FROM known_sender WHERE address = \'{sender}\'')
                conn.commit()
            except Exception as e:
                logger.error(f'{e} in SETUNKNOWN operation for address {sender}')
                conn.rollback()

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
            init_db()

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


