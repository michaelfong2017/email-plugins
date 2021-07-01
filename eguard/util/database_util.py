import datetime

# Init db
def init_db(conn, USER_EMAILS, logger=None):
    start_time = datetime.datetime.now()

    for user_email in USER_EMAILS:
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS '{user_email}_known_sender' (address TEXT PRIMARY KEY NOT NULL);"""
        )
        conn.commit()

    conn.execute(
        """CREATE TABLE IF NOT EXISTS junk_sender (address TEXT PRIMARY KEY NOT NULL);"""
    )
    conn.commit()
    
    if logger is not None:
        logger.info(
            f"Time elapsed for initializing the database: {datetime.datetime.now() - start_time}"
        )


# Insert the address to known sender
def insert_address_to_known_sender(user_email, address, conn, logger=None):
    try:
        conn.execute(f"""INSERT INTO '{user_email}_known_sender' (address) VALUES ({address});""")
        conn.commit()
    except Exception as e:
        if logger is not None:
            logger.error(f"{e} in SET KNOWN operation for address {address}")
        conn.rollback()


# Delete the address from known sender
def delete_address_from_known_sender(user_email, address, conn, logger=None):
    try:
        conn.execute(f"""DELETE FROM '{user_email}_known_sender' WHERE address = {address};""")
        conn.commit()
    except Exception as e:
        if logger is not None:
            logger.error(f"{e} in UNSET KNOWN operation for address {address}")
        conn.rollback()


# Find if address exists in known sender
def is_address_exists_in_known_sender(user_email, address, conn, logger=None):
    try:
        cursor = conn.execute(
            f"""SELECT count(*) FROM '{user_email}_known_sender' WHERE address = {address};"""
        )
        records = cursor.fetchall()
        match_count = records[0][0]

        if match_count == 0:
            return False
        else:
            return True

    except Exception as e:
        if logger is not None:
            logger.error(f"{e} in CHECK KNOWN operation for address {address}")
        return None


# Insert the address to junk sender
def insert_address_to_junk_sender(address, conn, logger=None):
    try:
        conn.execute(f"""INSERT INTO junk_sender (address) VALUES ({address});""")
        conn.commit()
    except Exception as e:
        if logger is not None:
            logger.error(f"{e} in SET JUNK operation for address {address}")
        conn.rollback()


# Delete the address from junk sender
def delete_address_from_junk_sender(address, conn, logger=None):
    try:
        conn.execute(f"""DELETE FROM junk_sender WHERE address = {address};""")
        conn.commit()
    except Exception as e:
        if logger is not None:
            logger.error(f"{e} in UNSET JUNK operation for address {address}")
        conn.rollback()


# Find if address exists in junk sender
def is_address_exists_in_junk_sender(address, conn, logger=None):
    try:
        cursor = conn.execute(
            f"""SELECT count(*) FROM junk_sender WHERE address = {address};"""
        )
        records = cursor.fetchall()
        match_count = records[0][0]

        if match_count == 0:
            return False
        else:
            return True

    except Exception as e:
        if logger is not None:
            logger.error(f"{e} in CHECK JUNK operation for address {address}")
        return None
