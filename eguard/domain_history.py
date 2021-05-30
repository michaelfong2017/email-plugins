import os
import time

import email
import re

import logging

from daemonize import Daemonize

## sqlite3
import sqlite3

import datetime

## Handle arguments
import argparse

## Read config file
import toml

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Debug level set from logging.WARNING to logging.DEBUG')
parser.add_argument('-s', '--sleep', type=int, help='Daemon process sleep duration (in seconds) between loops')
args = parser.parse_args()


SLEEP_DURATION = args.sleep if args.sleep else 1 # second, default is 5

## Daemonize
pid = ".process.pid"

logger = logging.getLogger(__name__)

if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.CRITICAL)

if not len(logger.handlers) == 0:
    logger.handlers.clear()

fh = logging.FileHandler("process.log", "w")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

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
        if ('S' in flags):
            # If message is read, mark as recognized in database.
            with open(filepath, "r+") as f:
                msg = email.message_from_file(f) # Whole email message including both headers and content

                parser = email.parser.HeaderParser()
                headers = parser.parsestr(msg.as_string())

                # for h in headers.items(): # Get all header information, this can be commented since we now just need to identify the sender
                #     print(h)


                # Remove banner from Subject if exists
                subject = headers['Subject']
                if subject.startswith('[FROM NEW SENDER] '):
                    headers.replace_header('Subject', subject.replace('[FROM NEW SENDER] ',''))
                    f.seek(0)
                    f.write(headers.as_string())
                    f.truncate()
                else:
                    pass

                # Find address from the message
                sender = headers['From']

                m = re.search(r"\<(.*?)\>", sender) # In case sender is something like '"Chan, Tai Man" <ctm@gmail.com>' instead of 'ctm@gmail.com'
                if m != None:
                    sender = m.group(1)

                logger.info(f"Sender of this email: {sender}")

                address = f"\'{sender}\'"

                # Insert the address to database
                try:
                    conn.execute(f'''INSERT INTO known_sender (address) VALUES ({address});''')
                    conn.commit()
                except Exception as e:
                    logger.error(f'{e} in SETKNOWN operation for address {address}')
                    conn.rollback()

            # Rename file
            new_file_size = os.stat(filepath).st_size

            new_filename = re.sub(r',S=[0-9]*,', f',S={new_file_size},', inbox_mail)

            os.rename(filepath, os.path.join(INBOX_DIR, new_filename))

        else:
            # If message is unread, add a warning banner to the subject.
            with open(filepath, "r+") as f:
                msg = email.message_from_file(f) # Whole email message including both headers and content

                parser = email.parser.HeaderParser()
                headers = parser.parsestr(msg.as_string())


                # Find address from the message
                sender = headers['From']

                m = re.search(r"\<(.*?)\>", sender) # In case sender is something like '"Chan, Tai Man" <ctm@gmail.com>' instead of 'ctm@gmail.com'
                if m != None:
                    sender = m.group(1)

                logger.info(f"Sender of this email: {sender}")

                # Add banner to Subject if record does not exist in database
                try:
                    cursor = conn.execute(f'SELECT count(*) FROM known_sender WHERE address = \'{sender}\'')
                    records = cursor.fetchall()

                    match_count = records[0][0]
                    logger.info(f'match_count is {match_count}')

                    if match_count == 0:
                        subject = headers['Subject']
                        if subject.startswith('[FROM NEW SENDER] '):
                            pass
                        else:
                            headers.replace_header('Subject', "[FROM NEW SENDER] " + subject)
                            f.seek(0)
                            f.write(headers.as_string())
                            f.truncate()
                    else:
                        pass

                except Exception as e:
                    logger.error(f'{e} in CHECK operation for address {sender}')


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

daemon = Daemonize(app="domain_history", pid=pid, action=main, logger=logger, keep_fds=keep_fds)
daemon.start()


