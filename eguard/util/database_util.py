# Insert the address to known sender
def insert_address_to_known_sender(address, conn, logger=None):
    try:
        conn.execute(f'''INSERT INTO known_sender (address) VALUES ({address});''')
        conn.commit()
    except Exception as e:
        if logger is not None:
            logger.error(f'{e} in SETKNOWN operation for address {address}')
        conn.rollback()


# Delete the address from known sender
def delete_address_from_known_sender(address, conn, logger=None):
    try:
        conn.execute(f'''DELETE FROM known_sender WHERE address = {address};''')
        conn.commit()
    except Exception as e:
        if logger is not None:
            logger.error(f'{e} in SETUNKNOWN operation for address {address}')
        conn.rollback()


# Find if address exists in known sender
def is_address_exists_in_known_sender(address, conn, logger=None):
    try:
        cursor = conn.execute(f'''SELECT count(*) FROM known_sender WHERE address = {address};''')
        records = cursor.fetchall()
        match_count = records[0][0]

        if match_count == 0:
            return False
        else:
            return True

    except Exception as e:
        if logger is not None:
            logger.error(f'{e} in CHECK operation for address {address}')
        return None