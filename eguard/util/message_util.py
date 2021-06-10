# Email
import email
from email import policy
from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import re

import os

BANNER_PLAIN = '''Caution: The domain of email sender is first seen.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  
注意：這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。

'''
BANNER_HTML = '''<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff4444; padding: 5px;">Caution: The domain of email sender is first seen. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;<br /><span>注意：這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span></p>\n'''


def find_body_plain_and_html_from_message(msg):
    body_plain = ""
    body_html = ""
    
    is_multipart = False
    if msg.is_multipart(): # Currently, this is the case
        is_multipart = True

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

    return body_plain, body_html, is_multipart


# Remove banner from Subject if exists
def remove_banner_from_subject(filepath):
    with open(filepath, "r+") as f:
        # Get msg and headers from file for further processing
        msg = email.message_from_file(f) # Whole email message including both headers and content
        parser = email.parser.HeaderParser()
        headers = parser.parsestr(msg.as_string())

        subject = headers['Subject']
        if subject.startswith('[FROM NEW SENDER] '):
            headers.replace_header('Subject', subject.replace('[FROM NEW SENDER] ',''))
            f.seek(0)
            f.write(headers.as_string())
            f.truncate()
        else:
            pass
    

# Add banner to Subject
def add_banner_to_subject(filepath):
    with open(filepath, "r+") as f:
        # Get msg and headers from file for further processing
        msg = email.message_from_file(f) # Whole email message including both headers and content
        parser = email.parser.HeaderParser()
        headers = parser.parsestr(msg.as_string())

        subject = headers['Subject']
        if subject.startswith('[FROM NEW SENDER] '):
            pass
        else:
            headers.replace_header('Subject', "[FROM NEW SENDER] " + subject)
            f.seek(0)
            f.write(headers.as_string())
            f.truncate()

# Find address from the message
def find_address_from_message(filepath):
    with open(filepath, "r+") as f:
        # Get msg and headers from file for further processing
        msg = email.message_from_file(f) # Whole email message including both headers and content
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
    

# Prepend warning banner to mail body (have to handle for both plain and html)
def prepend_banner_to_body(filepath):
    with open(filepath, "r+") as f:
        # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
        msg = email.message_from_file(f, policy=policy.default) # Whole email message including both headers and content

        new_msg = MIMEMultipart('alternative')
        # Exclude "Content-Type" and "MIME-Version" because MIMEMultipart('alternative') already contains them.
        # Exclude "Content-Transfer-Encoding" because 'alternative' does not have this but plain text email has this.
        headers = list((k, v) for (k, v) in msg.items() if k not in ("Content-Type", "MIME-Version", "Content-Transfer-Encoding"))

        for k, v in headers:
            new_msg[k] = v

        for k, v in headers:
            del msg[k]

        # Create the body of the message from the original msg (a plain-text and an HTML version).
        body_plain, body_html, is_multipart = find_body_plain_and_html_from_message(msg)

        banner_plain = BANNER_PLAIN

        if is_multipart:
            body_plain = body_plain.decode("utf-8")
            body_html = body_html.decode("utf-8")
            html = f'''<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head><body style=\'font-size: 10pt; font-family: Verdana,Geneva,sans-serif\'>\n{BANNER_HTML}{body_html}</body></html>\n'''
        else:
            html = f'''<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head><body style=\'font-size: 10pt; font-family: Verdana,Geneva,sans-serif\'>\n{BANNER_HTML}<p>{body_plain}</p>\n</body></html>\n'''

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(banner_plain + body_plain, 'plain')
        part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        new_msg.attach(part1)
        new_msg.attach(part2)

        
        f.seek(0)
        f.write(new_msg.as_string())
        f.truncate()


# Remove the previously prepended warning banner from mail body (have to handle for both plain and html)
def remove_banner_from_body(filepath):
    with open(filepath, "r+") as f:
        # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
        msg = email.message_from_file(f, policy=policy.default) # Whole email message including both headers and content

        # If msg is not multipart (e.g. plain text only), it is obvious that no warning banner exists and needs to be removed.
        if msg.is_multipart() == False:
            return

        new_msg = MIMEMultipart('alternative')
        # Exclude "Content-Type" and "MIME-Version" because MIMEMultipart('alternative') already contains them.
        # Exclude "Content-Transfer-Encoding" because 'alternative' does not have this but plain text email has this.
        headers = list((k, v) for (k, v) in msg.items() if k not in ("Content-Type", "MIME-Version", "Content-Transfer-Encoding"))

        for k, v in headers:
            new_msg[k] = v

        for k, v in headers:
            del msg[k]

        # Create the body of the message from the original msg (a plain-text and an HTML version).
        body_plain, body_html, _ = find_body_plain_and_html_from_message(msg)
        body_plain = body_plain.decode("utf-8")
        body_html = body_html.decode("utf-8")

        new_body_plain = re.sub(BANNER_PLAIN, '', body_plain)
        new_body_html = re.sub(BANNER_HTML, '', body_html)

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(new_body_plain, 'plain')
        part2 = MIMEText(new_body_html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        new_msg.attach(part1)
        new_msg.attach(part2)

        
        f.seek(0)
        f.write(new_msg.as_string())
        f.truncate()