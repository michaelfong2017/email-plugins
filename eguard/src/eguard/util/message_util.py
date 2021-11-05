# Email
import email
from email import policy
from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import os
import shutil
import logging

logger = logging.getLogger()

########
# BEGIN
# Current warnings
########
UNKNOWN_SUBJECT = """[FROM NEW SENDER] """
JUNK_SUBJECT = """[JUNK MAIL] """
UNKNOWN_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff7400; padding: 5px;"><span>注意：<br />這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />CAUTION:<br/>The domain of email sender is first seen. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""
JUNK_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff4444; padding: 5px;"><span>注意：<br />這是曾被舉報為垃圾發件人的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />WARNING:<br />The domain of email sender was reported as a junk sender. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""

UNKNOWN_BANNER_PLAIN = """注意：
這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
CAUTION: 
The domain of email sender is first seen.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""

JUNK_BANNER_PLAIN = """警告：
這是曾被舉報為垃圾發件人的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
WARNING: 
The domain of email sender was reported as a junk sender.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""
########
# Current warnings
# END
########

########
# BEGIN
# Warnings in previous version
# This is required when updating the warning banners.
# Otherwise, all emails are messed up.
########
PREV_UNKNOWN_SUBJECT = """[FROM NEW SENDER] """
PREV_JUNK_SUBJECT = """[JUNK MAIL] """
PREV_UNKNOWN_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff7400; padding: 5px;"><span>注意：<br />這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />CAUTION:<br/>The domain of email sender is first seen. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""
PREV_JUNK_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff4444; padding: 5px;"><span>注意：<br />這是曾被舉報為垃圾發件人的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />WARNING:<br />The domain of email sender was reported as a junk sender. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""

PREV_UNKNOWN_BANNER_PLAIN = """注意：
這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
CAUTION: 
The domain of email sender is first seen.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""

PREV_JUNK_BANNER_PLAIN = """警告：
這是曾被舉報為垃圾發件人的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
WARNING: 
The domain of email sender was reported as a junk sender.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""
########
# Warnings in previous version
# END
########


def find_body_plain_and_html_from_message(msg):
    body_plain = ""
    body_html = ""

    is_multipart = False
    if msg.is_multipart():  # Currently, this is the case
        is_multipart = True

        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition"))

            # skip any text/plain (txt) attachments
            if ctype == "text/plain" and "attachment" not in cdispo:
                body_plain = part.get_payload(decode=True)  # decode
            if ctype == "text/html" and "attachment" not in cdispo:
                body_html = part.get_payload(decode=True)  # decode
    # not multipart - i.e. plain text, no attachments, keeping fingers crossed
    else:
        body_plain = msg.get_payload()

    return body_plain, body_html, is_multipart


# Remove banner from Subject if exists
def remove_banner_from_subject(filepath, is_junk=False):
    if is_junk:
        SUBJECT = JUNK_SUBJECT
        PREV_SUBJECT = PREV_JUNK_SUBJECT
    else:
        SUBJECT = UNKNOWN_SUBJECT
        PREV_SUBJECT = PREV_UNKNOWN_SUBJECT

    try:
        with open(filepath, "r+") as f:
            # Get msg and headers from file for further processing
            msg = email.message_from_file(
                f
            )  # Whole email message including both headers and content
            parser = email.parser.HeaderParser()
            headers = parser.parsestr(msg.as_string())

            subject = headers["Subject"]
            if subject:
                if SUBJECT in subject:
                    headers.replace_header("Subject", subject.replace(SUBJECT, ""))
                # Start with subject of the previous version instead of the current version.
                # That's the case subject has been updated and migration is required.
                elif PREV_SUBJECT in subject:
                    headers.replace_header("Subject", subject.replace(PREV_SUBJECT, ""))
                f.seek(0)
                f.write(headers.as_string())
                f.truncate()
            else:
                pass

    except Exception as e:
        logger.error(e)


# Add banner to Subject
def add_banner_to_subject(filepath, is_junk=False):
    if is_junk:
        SUBJECT = JUNK_SUBJECT
        PREV_SUBJECT = PREV_JUNK_SUBJECT
    else:
        SUBJECT = UNKNOWN_SUBJECT
        PREV_SUBJECT = PREV_UNKNOWN_SUBJECT

    try:
        with open(filepath, "r+") as f:
            # Get msg and headers from file for further processing
            msg = email.message_from_file(
                f
            )  # Whole email message including both headers and content
            parser = email.parser.HeaderParser()
            headers = parser.parsestr(msg.as_string())

            subject = headers["Subject"]

            if subject:
                if subject.startswith(SUBJECT):
                    pass
                else:
                    # Start with subject of the previous version instead of the current version.
                    # That's the case subject has been updated and migration is required.
                    if subject.startswith(PREV_SUBJECT):
                        headers.replace_header(
                            "Subject", subject.replace(PREV_SUBJECT, SUBJECT)
                        )
                    else:
                        headers.replace_header("Subject", SUBJECT + subject)
                    f.seek(0)
                    f.write(headers.as_string())
                    f.truncate()
            else:
                headers.add_header("Subject", SUBJECT)
                f.seek(0)
                f.write(headers.as_string())
                f.truncate()

    except Exception as e:
        logger.error(e)


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


# Rename file based on size
def rename_file_based_on_size(MAIL_DIR, filename):
    filepath = os.path.join(MAIL_DIR, filename)

    try:
        new_file_size = os.stat(filepath).st_size
        new_filename = re.sub(r",S=[0-9]*,", f",S={new_file_size},", filename)
        os.rename(filepath, os.path.join(MAIL_DIR, new_filename))
        return new_filename

    except Exception as e:
        logger.error(e)

    return filename


# Rename new mail based on size, for new mail only, append :2,
def rename_new_mail_based_on_size(MAIL_DIR, filename):
    filepath = os.path.join(MAIL_DIR, filename)

    try:
        new_file_size = os.stat(filepath).st_size
        new_filename = re.sub(r",S=[0-9]*,", f",S={new_file_size},", filename)
        new_filename += ":2,"
        os.rename(filepath, os.path.join(MAIL_DIR, new_filename))
        return new_filename

    except Exception as e:
        logger.error(e)

    return filename


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
        except Exception as e:
            logger.error(e)

    else:
        dest_filepath = os.path.join(dest_dir, filename)

        try:
            shutil.move(os.path.join(src_dir, filename), dest_filepath)
        except Exception as e:
            logger.error(e)


# Remove the previously prepended warning banner from mail body (have to handle for both plain and html)
def remove_banner_from_body(filepath, is_junk=False):
    if is_junk:
        BANNER_PLAIN = JUNK_BANNER_PLAIN
        BANNER_HTML = JUNK_BANNER_HTML
        PREV_BANNER_PLAIN = PREV_JUNK_BANNER_PLAIN
        PREV_BANNER_HTML = PREV_JUNK_BANNER_HTML
    else:
        BANNER_PLAIN = UNKNOWN_BANNER_PLAIN
        BANNER_HTML = UNKNOWN_BANNER_HTML
        PREV_BANNER_PLAIN = PREV_UNKNOWN_BANNER_PLAIN
        PREV_BANNER_HTML = PREV_UNKNOWN_BANNER_HTML

    try:
        with open(filepath, "r+") as f:
            # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
            msg = email.message_from_file(
                f, policy=policy.default
            )  # Whole email message including both headers and content

            # If msg is not multipart (e.g. plain text only), it is obvious that no warning banner exists and needs to be removed.
            if msg.is_multipart() == False:
                return

            new_msg = MIMEMultipart("alternative")
            # Exclude "Content-Type" and "MIME-Version" because MIMEMultipart('alternative') already contains them.
            # Exclude "Content-Transfer-Encoding" because 'alternative' does not have this but plain text email has this.
            headers = list(
                (k, v)
                for (k, v) in msg.items()
                if k
                not in ("Content-Type", "MIME-Version", "Content-Transfer-Encoding")
            )

            for k, v in headers:
                new_msg[k] = v

            for k, v in headers:
                del msg[k]

            # Create the body of the message from the original msg (a plain-text and an HTML version).
            body_plain, body_html, _ = find_body_plain_and_html_from_message(msg)
            if type(body_plain) == bytes:
                body_plain = body_plain.decode("utf-8")
            if type(body_html) == bytes:
                body_html = body_html.decode("utf-8")

            # The lines below remove existing banner(s) first.
            #### BEGIN remove ####
            if re.search(f"{BANNER_PLAIN}", body_plain):
                body_plain = re.sub(BANNER_PLAIN, "", body_plain)
            # Start with subject of the previous version instead of the current version.
            # That's the case subject has been updated and migration is required.
            elif re.search(f"{PREV_BANNER_PLAIN}", body_plain):
                body_plain = re.sub(PREV_BANNER_PLAIN, "", body_plain)

            if re.search(f"{BANNER_HTML}", body_html):
                body_html = re.sub(BANNER_HTML, "", body_html)
            # Start with subject of the previous version instead of the current version.
            # That's the case subject has been updated and migration is required.
            elif re.search(f"{PREV_BANNER_HTML}", body_html):
                body_html = re.sub(PREV_BANNER_HTML, "", body_html)
            #### END remove ####

            # Record the MIME types of both parts - text/plain and text/html.
            part1 = MIMEText(body_plain, "plain")
            part2 = MIMEText(body_html, "html")

            # Attach parts into message container.
            # According to RFC 2046, the last part of a multipart message, in this case
            # the HTML message, is best and preferred.
            new_msg.attach(part1)
            new_msg.attach(part2)

            f.seek(0)
            f.write(new_msg.as_string())
            f.truncate()

    except Exception as e:
        logger.error(e)


# Prepend warning banner to mail body (have to handle for both plain and html)
def add_banner_to_body(filepath, is_junk=False):
    if is_junk:
        BANNER_PLAIN = JUNK_BANNER_PLAIN
        BANNER_HTML = JUNK_BANNER_HTML
        PREV_BANNER_PLAIN = PREV_JUNK_BANNER_PLAIN
        PREV_BANNER_HTML = PREV_JUNK_BANNER_HTML
    else:
        BANNER_PLAIN = UNKNOWN_BANNER_PLAIN
        BANNER_HTML = UNKNOWN_BANNER_HTML
        PREV_BANNER_PLAIN = PREV_UNKNOWN_BANNER_PLAIN
        PREV_BANNER_HTML = PREV_UNKNOWN_BANNER_HTML

    try:
        with open(filepath, "r+") as f:
            # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
            msg = email.message_from_file(
                f, policy=policy.default
            )  # Whole email message including both headers and content

            new_msg = MIMEMultipart("alternative")
            # Exclude "Content-Type" and "MIME-Version" because MIMEMultipart('alternative') already contains them.
            # Exclude "Content-Transfer-Encoding" because 'alternative' does not have this but plain text email has this.
            headers = list(
                (k, v)
                for (k, v) in msg.items()
                if k
                not in ("Content-Type", "MIME-Version", "Content-Transfer-Encoding")
            )

            for k, v in headers:
                new_msg[k] = v

            for k, v in headers:
                del msg[k]

            # Create the body of the message from the original msg (a plain-text and an HTML version).
            body_plain, body_html, is_multipart = find_body_plain_and_html_from_message(
                msg
            )

            banner_plain = BANNER_PLAIN

            # If not multipart, for example, plain text only.
            if is_multipart:
                if type(body_plain) == bytes:
                    body_plain = body_plain.decode("utf-8")
                if type(body_html) == bytes:
                    body_html = body_html.decode("utf-8")

                # The lines below remove existing banner(s) first.
                #### BEGIN remove ####
                if re.search(f"{BANNER_PLAIN}", body_plain):
                    body_plain = re.sub(BANNER_PLAIN, "", body_plain)
                # Start with subject of the previous version instead of the current version.
                # That's the case subject has been updated and migration is required.
                elif re.search(f"{PREV_BANNER_PLAIN}", body_plain):
                    body_plain = re.sub(PREV_BANNER_PLAIN, "", body_plain)

                if re.search(f"{BANNER_HTML}", body_html):
                    body_html = re.sub(BANNER_HTML, "", body_html)
                # Start with subject of the previous version instead of the current version.
                # That's the case subject has been updated and migration is required.
                elif re.search(f"{PREV_BANNER_HTML}", body_html):
                    body_html = re.sub(PREV_BANNER_HTML, "", body_html)
                #### END remove #### 

                html = f"""{BANNER_HTML}{body_html}"""
            else:
                html = f"""{BANNER_HTML}<p>{body_plain}</p>"""

            # Record the MIME types of both parts - text/plain and text/html.
            part1 = MIMEText(banner_plain + body_plain, "plain")
            part2 = MIMEText(html, "html")

            # Attach parts into message container.
            # According to RFC 2046, the last part of a multipart message, in this case
            # the HTML message, is best and preferred.
            new_msg.attach(part1)
            new_msg.attach(part2)

            f.seek(0)
            f.write(new_msg.as_string())
            f.truncate()

    except Exception as e:
        logger.error(e)


"""
Remove all subject and body banners before demanding a banner.
Logically, for a mail, multiple banners in arbitrary positions are removed
at once.
"""


def remove_all_banners(filepath):
    remove_banner_from_subject(filepath, is_junk=True)
    remove_banner_from_body(filepath, is_junk=True)
    remove_banner_from_subject(filepath, is_junk=False)
    remove_banner_from_body(filepath, is_junk=False)


# %%
# import email


# def test():
#     filepath = "/mailu/mail/cs@michaelfong.co/cur/1636096665.M141405P6455.f9db57f63506,S=975,W=1000:2,S"
#     filepath2 = "/mailu/mail/cs@michaelfong.co/cur/1636096686.M399989P6455.f9db57f63506,S=847,W=868:2,S"
#     filepath3 = "/mailu/mail/cs@michaelfong.co/cur/1636096711.M127784P6455.f9db57f63506,S=1579,W=1621:2,S"
#     filepath4 = "/mailu/mail/cs@michaelfong.co/cur/1636096733.M54203P6455.f9db57f63506,S=1111,W=1139:2,S"
#     filepath5 = "/mailu/mail/cs@michaelfong.co/cur/1636096842.M496581P6574.f9db57f63506,S=371083,W=375942:2,S"
#     filepath6 = "/mailu/mail/cs@michaelfong.co/cur/1636096884.M878900P6574.f9db57f63506,S=370608,W=375450:2,S"
#     filepath7 = "/mailu/mail/cs@michaelfong.co/cur/1636096954.M596759P6644.f9db57f63506,S=996569,W=1009544:2,S"
#     filepath8 = "/mailu/mail/cs@michaelfong.co/cur/1636096982.M830818P6644.f9db57f63506,S=996420,W=1009390:2,S"
#     filepath9 = "/mailu/mail/cs@michaelfong.co/cur/1636097029.M531700P6644.f9db57f63506,S=997175,W=1010168:2,S"
#     filepath10 = "/mailu/mail/cs@michaelfong.co/cur/1636097060.M607977P6644.f9db57f63506,S=996705,W=1009684:2,S"
#     filepath11 = "/mailu/mail/cs@michaelfong.co/cur/1636097114.M95706P6644.f9db57f63506,S=1366710,W=1384521:2,S"
#     filepath12 = "/mailu/mail/cs@michaelfong.co/cur/1636097155.M42624P6644.f9db57f63506,S=1366202,W=1383995:2,S"
#     try:
#         for path in [
#             filepath,
#             filepath2,
#             filepath3,
#             filepath4,
#             filepath5,
#             filepath6,
#             filepath7,
#             filepath8,
#             filepath9,
#             filepath10,
#             filepath11,
#             filepath12,
#         ]:
#             with open(filepath3, "r+") as f:
#                 # Get msg and headers from file for further processing
#                 msg = email.message_from_file(
#                     f
#                 )  # Whole email message including both headers and content
#                 parser = email.parser.HeaderParser()
#                 headers = parser.parsestr(msg.as_string())

#                 subject = headers["Subject"]
#                 # print(subject)
#                 # print("\n")

#                 # print(headers["Content-Type"])
#                 # print("\n")

#                 for part in msg.walk():
#                     ctype = part.get_content_type()
#                     charset = part.get_content_charset()
#                     cdispo = part.get_content_disposition()
#                     print(f"ctype: {ctype}")
#                     # print(f"charset: {charset}")
#                     # print(f"cdispo: {cdispo}")
#                     # print(part.get_payload()[:20] if len(part.get_payload()) > 20 else part.get_payload())
#                     # if ctype == "multipart/mixed" or ctype == "multipart/alternative" or ctype == "multipart/related":
#                     #     print(part.get_payload(decode=True))
#                     # else:
#                     #     print(part.get_payload(decode=True)[:20] if len(part.get_payload(decode=True)) > 20 else part.get_payload(decode=True))
#                     if not ctype.startswith("multipart"):
#                         print(part.get_payload(decode=True).decode("utf-8"))
#                     print("\n")
#                     # cdispo = str(part.get("Content-Disposition"))

#                     # skip any text/plain (txt) attachments
#                     # if ctype == "text/plain" and "attachment" not in cdispo:
#                     #     body_plain = part.get_payload(decode=True)  # decode
#                     # if ctype == "text/html" and "attachment" not in cdispo:
#                     #     body_html = part.get_payload(decode=True)  # decode

#                 # if subject:
#                 #     if subject.startswith(SUBJECT):
#                 #         pass
#                 #     else:
#                 #         # Start with subject of the previous version instead of the current version.
#                 #         # That's the case subject has been updated and migration is required.
#                 #         if subject.startswith(PREV_SUBJECT):
#                 #             headers.replace_header(
#                 #                 "Subject", subject.replace(PREV_SUBJECT, SUBJECT)
#                 #             )
#                 #         else:
#                 #             headers.replace_header("Subject", SUBJECT + subject)
#                 #         f.seek(0)
#                 #         f.write(headers.as_string())
#                 #         f.truncate()
#                 # else:
#                 #     headers.add_header("Subject", SUBJECT)
#                 #     f.seek(0)
#                 #     f.write(headers.as_string())
#                 #     f.truncate()

#     except Exception as e:
#         pass


# test()
# # %%
# import re
# import quopri

# BANNER = "[FROM NEW SENDER] "

# subject = "=?UTF-8?Q?=E5=B0=B1=E5=92=81plain_text_test_email?="
# regex = r"=\?UTF-8\?Q\?(.*?)\?="
# match = re.match(regex, subject)

# # (c) No subject
# if subject is None:
#     # ...
#     pass

# else:
#     # (b) Has subject with chinese characters
#     if match:
#         content = match.groups()[0]
#         decoded = quopri.decodestring(content, header=True).decode("utf-8")
#         encoded = quopri.encodestring(
#             (BANNER + decoded).encode("utf-8"), header=True
#         ).decode("utf-8")
#         new_subject = f"=?UTF-8?Q?{encoded}?="

#     # (a) Has subject without chinese characters
#     else:
#         new_subject = f"{BANNER}{subject}"

# print(new_subject)
# %%
