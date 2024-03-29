import sqlite3
import os
import datetime
import logging

logger = logging.getLogger()


class SqliteSenderRepository:
    def connect_db_if_not(self):
        try:
            if (
                self.conn
                and datetime.datetime.now() - datetime.timedelta(seconds=1800)
                > self.conn_time
            ):
                self.conn.close()
                logger.info(f"{self}: closed db.")
                del self.conn
                logger.info(f"{self}: connect db now.")
                self.conn = sqlite3.connect(
                    os.path.join(os.path.abspath("."), "data/eguard.db"),
                    check_same_thread=False,
                )
                self.conn_time = datetime.datetime.now()

        except (AttributeError) as e:
            logger.info(f"{self}: connect db now.")
            self.conn = sqlite3.connect(
                os.path.join(os.path.abspath("."), "data/eguard.db"),
                check_same_thread=False,
            )
            self.conn_time = datetime.datetime.now()

    def create_known_sender_table_if_not_exists(self, user_email):
        self.connect_db_if_not()

        try:
            self.conn.execute(f"""SELECT count(*) FROM `{user_email}_known_sender`""")

        except (sqlite3.OperationalError) as e:
            logger.info(f"{self}: create table `{user_email}_known_sender` now.")
            self.conn.execute(
                f"""CREATE TABLE IF NOT EXISTS `{user_email}_known_sender` (address TEXT PRIMARY KEY NOT NULL)"""
            )
            self.conn.commit()

    def create_junk_sender_table_if_not_exists(self):
        self.connect_db_if_not()

        try:
            self.conn.execute(f"""SELECT count(*) FROM junk_sender""")

        except (sqlite3.OperationalError) as e:
            logger.info(f"{self}: create table junk_sender now.")
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS junk_sender (address TEXT PRIMARY KEY NOT NULL)"""
            )
            self.conn.commit()

    # Insert the address to known sender
    def insert_address_to_known_sender(self, user_email, address):
        self.create_known_sender_table_if_not_exists(user_email)

        try:
            self.conn.execute(
                f"""INSERT INTO `{user_email}_known_sender` (address) VALUES ({address})"""
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    # Delete the address from known sender
    def delete_address_from_known_sender(self, user_email, address):
        self.create_known_sender_table_if_not_exists(user_email)

        try:
            self.conn.execute(
                f"""DELETE FROM `{user_email}_known_sender` WHERE address = {address}"""
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    # Find if address exists in known sender
    def is_address_exists_in_known_sender(self, user_email, address):
        self.create_known_sender_table_if_not_exists(user_email)

        try:
            cursor = self.conn.execute(
                f"""SELECT count(*) FROM `{user_email}_known_sender` WHERE address = {address}"""
            )
            records = cursor.fetchall()
            match_count = records[0][0]

            if match_count == 0:
                return False
            else:
                return True

        except Exception as e:
            logger.error(f"{e} in CHECK KNOWN operation for address {address}")
            return None

    # Select addresses from known sender
    ## Return a set
    def select_addresses_from_known_sender(self, user_email):
        self.connect_db_if_not()

        try:
            cursor = self.conn.execute(f"""SELECT * FROM `{user_email}_known_sender`""")
            records = cursor.fetchall()
            return set(record[0] for record in records)

        except Exception as e:
            # logging.getLogger("stat").error(e)
            return set()

    # Insert the address to junk sender
    def insert_address_to_junk_sender(self, address):
        self.create_junk_sender_table_if_not_exists()

        try:
            self.conn.execute(
                f"""INSERT INTO junk_sender (address) VALUES ({address})"""
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    # Delete the address from junk sender
    def delete_address_from_junk_sender(self, address):
        self.create_junk_sender_table_if_not_exists()

        try:
            self.conn.execute(f"""DELETE FROM junk_sender WHERE address = {address}""")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    # Find if address exists in junk sender
    def is_address_exists_in_junk_sender(self, address):
        self.create_junk_sender_table_if_not_exists()

        try:
            cursor = self.conn.execute(
                f"""SELECT count(*) FROM junk_sender WHERE address = {address}"""
            )
            records = cursor.fetchall()
            match_count = records[0][0]

            if match_count == 0:
                return False
            else:
                return True

        except Exception as e:
            logger.error(f"{e} in CHECK JUNK operation for address {address}")
            return None

    # Select addresses from junk sender
    ## Return a set
    def select_addresses_from_junk_sender(self):
        self.connect_db_if_not()

        try:
            cursor = self.conn.execute(f"""SELECT * FROM junk_sender""")
            records = cursor.fetchall()
            return set(record[0] for record in records)

        except Exception as e:
            # logging.getLogger("stat").error(e)
            return set()

    """
    List of backup mails
    """
    def create_backup_mail_list_table_if_not_exists(self, user_email):
        self.connect_db_if_not()

        try:
            self.conn.execute(f"""SELECT count(*) FROM `{user_email}_backup_mail_list`""")

        except (sqlite3.OperationalError) as e:
            logger.info(f"{self}: create table `{user_email}_backup_mail_list` now.")
            self.conn.execute(
                f"""CREATE TABLE IF NOT EXISTS `{user_email}_backup_mail_list` (uid TEXT PRIMARY KEY NOT NULL)"""
            )
            self.conn.commit()

    # Insert the uid to backup mail list
    def insert_uid_to_backup_mail_list(self, user_email, uid):
        self.create_backup_mail_list_table_if_not_exists(user_email)

        try:
            self.conn.execute(
                f"""INSERT INTO `{user_email}_backup_mail_list` (uid) VALUES ({uid})"""
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    # Find if uid exists in backup mail list
    def is_uid_exists_in_backup_mail_list(self, user_email, uid):
        self.create_backup_mail_list_table_if_not_exists(user_email)

        try:
            cursor = self.conn.execute(
                f"""SELECT count(*) FROM `{user_email}_backup_mail_list` WHERE uid = {uid}"""
            )
            records = cursor.fetchall()
            match_count = records[0][0]

            if match_count == 0:
                return False
            else:
                return True

        except Exception as e:
            logger.error(f"{e} in IS EXISTS operation for uid {uid}")
            return None