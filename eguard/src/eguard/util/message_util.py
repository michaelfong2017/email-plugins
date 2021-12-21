# Email
import email
import re
import os
import shutil
import logging
import ntpath

logger = logging.getLogger()

# Find address from the message
def find_address_from_message(filepath):
    try:
        with open(filepath, "r+") as f:
            # Get msg and headers from file for further processing
            msg = email.message_from_file(
                f
            )  # Whole email message including both headers and content
            parser = email.parser.HeaderParser()
            headers = parser.parsestr(msg.as_string())

            sender = headers["From"]
            if sender != None:
                m = re.search(
                    r"\<(.*?)\>", sender
                )  # In case sender is something like '"Chan, Tai Man" <ctm@gmail.com>' instead of 'ctm@gmail.com'
                if m != None:
                    sender = m.group(1)
            address = f"'{sender}'"
            return address

    except Exception as e:
        logger.error(e)

# Move mail from source folder to destination folder
def move_to_folder(src_dir, dest_dir, filename, is_junk=False):
    if is_junk:
        flags = filename.split(",")[-1]
        new_flags = flags.replace("a", "")
        new_filename = f"{','.join(filename.split(',')[:-1])},{new_flags}"

        try:
            os.rename(
                os.path.join(src_dir, filename), os.path.join(src_dir, new_filename)
            )
            shutil.move(
                os.path.join(src_dir, new_filename),
                os.path.join(dest_dir, new_filename),
            )
            return os.path.join(dest_dir, new_filename)
        except Exception as e:
            logger.error(e)

    else:
        dest_filepath = os.path.join(dest_dir, filename)

        try:
            shutil.move(os.path.join(src_dir, filename), dest_filepath)
            return dest_filepath
        except Exception as e:
            logger.error(e)

def get_uid(filepath):
    return ntpath.basename(filepath).split(".")[0]