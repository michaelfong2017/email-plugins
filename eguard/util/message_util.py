import email

import re

import os

def find_body_plain_and_html_from_message(msg):
    body_plain = ""
    body_html = ""
    
    if msg.is_multipart(): # Currently, this is the case
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            
            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body_plain = part.get_payload(decode=True)  # decode
            if ctype == 'text/html' and 'attachment' not in cdispo:
                body_html = part.get_payload(decode=True)  # decode
    # not multipart - i.e. plain text, no attachments, keeping fingers crossed
    else:
        body_plain = msg.get_payload()

    return body_plain, body_html


# Remove banner from Subject if exists
def remove_banner_from_subject(msg, file, headers=None):
    if headers is None:
        parser = email.parser.HeaderParser()
        headers = parser.parsestr(msg.as_string())

    subject = headers['Subject']
    if subject.startswith('[FROM NEW SENDER] '):
        headers.replace_header('Subject', subject.replace('[FROM NEW SENDER] ',''))
        file.seek(0)
        file.write(headers.as_string())
        file.truncate
    else:
        pass
    
    return True

# Add banner to Subject
def add_banner_to_subject(msg, file, headers=None):
    if headers is None:
        parser = email.parser.HeaderParser()
        headers = parser.parsestr(msg.as_string())
        subject = headers['Subject']
        if subject.startswith('[FROM NEW SENDER] '):
            pass
        else:
            headers.replace_header('Subject', "[FROM NEW SENDER] " + subject)
            file.seek(0)
            file.write(headers.as_string())
            file.truncate()

# Find address from the message
def find_address_from_message(msg, headers=None):
    if headers is None:
        parser = email.parser.HeaderParser()
        headers = parser.parsestr(msg.as_string())

    sender = headers['From']
    m = re.search(r"\<(.*?)\>", sender) # In case sender is something like '"Chan, Tai Man" <ctm@gmail.com>' instead of 'ctm@gmail.com'
    if m != None:
        sender = m.group(1)
    address = f"\'{sender}\'"
    return address


# Rename file based on size
def rename_file_based_on_size(INBOX_DIR, inbox_mail):
    filepath = os.path.join(INBOX_DIR, inbox_mail)

    new_file_size = os.stat(filepath).st_size

    new_filename = re.sub(r',S=[0-9]*,', f',S={new_file_size},', inbox_mail)

    os.rename(filepath, os.path.join(INBOX_DIR, new_filename))
    
    return new_filename