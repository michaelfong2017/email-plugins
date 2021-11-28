#%%
import logging
import email
from email import policy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ntpath
import os
from pathlib import Path
import re
from shutil import copyfile
import quopri
import base64

logger = logging.getLogger()

OLD_UNKNOWN_SUBJECT_BANNER = """[FROM NEW SENDER] """
OLD_JUNK_SUBJECT_BANNER = """[JUNK MAIL] """
OLD_UNKNOWN_BANNER_PLAIN_TEXT = """注意：
這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
CAUTION: 
The domain of email sender is first seen.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""
OLD_UNKNOWN_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff7400; padding: 5px;"><span>注意：<br />這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />CAUTION:<br/>The domain of email sender is first seen. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""
OLD_JUNK_BANNER_PLAIN_TEXT = """警告：
這是曾被舉報為垃圾發件人的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
WARNING: 
The domain of email sender was reported as a junk sender.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""
OLD_JUNK_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff4444; padding: 5px;"><span>注意：<br />這是曾被舉報為垃圾發件人的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />WARNING:<br />The domain of email sender was reported as a junk sender. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""

##############################
##############################

UNKNOWN_SUBJECT_BANNER = """[🟠🟠FROM NEW SENDER🟠🟠] """
JUNK_SUBJECT_BANNER = """[🔴🔴JUNK MAIL🔴🔴] """
UNKNOWN_BANNER_PLAIN_TEXT = OLD_UNKNOWN_BANNER_PLAIN_TEXT
UNKNOWN_BANNER_HTML = OLD_UNKNOWN_BANNER_HTML
JUNK_BANNER_PLAIN_TEXT = OLD_JUNK_BANNER_PLAIN_TEXT
JUNK_BANNER_HTML = OLD_JUNK_BANNER_HTML


class MutableEmailFactory:
    @staticmethod
    def create_mutable_email(filepath):
        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                has_attachment = False
                has_alternative = False
                for part in msg.walk():
                    #### Check if attachment exists ####
                    if has_attachment == False:
                        if part.get_content_type() == "multipart/mixed":
                            has_attachment = True
                            continue
                    #### Check END ####
                    #### Start with the first part that is not "multipart/mixed".
                    if has_alternative == False:
                        if has_attachment:
                            if part.get_content_type() == "multipart/related":
                                return MutableEmailFB(filepath)
                            elif part.get_content_type() == "text/html":
                                return MutableEmailDB(filepath)
                            elif (
                                part.get_content_type() == "text/plain"
                                and part.get_content_charset() is not None
                            ):
                                return MutableEmailAB(filepath)
                            elif part.get_content_type() == "multipart/alternative":
                                has_alternative = True
                                continue
                            else:
                                return MutableEmailBB(filepath)
                        else:
                            if part.get_content_type() == "multipart/related":
                                return MutableEmailFA(filepath)
                            elif part.get_content_type() == "text/html":
                                return MutableEmailDA(filepath)
                            elif (
                                part.get_content_type() == "text/plain"
                                and part.get_content_charset() is None
                            ):
                                return MutableEmailBA(filepath)
                            elif (
                                part.get_content_type() == "text/plain"
                                and part.get_content_charset() is not None
                            ):
                                return MutableEmailAA(filepath)
                            elif part.get_content_type() == "multipart/alternative":
                                has_alternative = True
                                continue
                            else:
                                logger.error("Unexpected structure!")
                    #### Start with the first part that is not "multipart/mixed" END.
                    #### Start with the first part after "multipart/alternative".
                    if has_attachment:
                        if part.get_content_type() == "multipart/related":
                            return MutableEmailEB(filepath)
                    else:
                        if part.get_content_type() == "multipart/related":
                            return MutableEmailEA(filepath)
                    #### Start with the first part after "multipart/alternative" END.

                assert has_alternative == True
                if has_attachment:
                    return MutableEmailCB(filepath)
                else:
                    return MutableEmailCA(filepath)

        except Exception as e:
            logger.error(e)

        return MutableEmail(filepath)


class MutableEmail:
    default_html = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head><body style='font-size: 10pt; font-family: Verdana,Geneva,sans-serif'>

</body></html>
"""

    def wrap_text_with_default_html(self, text):
        return f"""<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head><body style='font-size: 10pt; font-family: Verdana,Geneva,sans-serif'>
<div>
<div><span>{text}</span></div>
</div>
</body></html>
"""

    def __init__(self, filepath):
        self.filepath = filepath

    def get_dir(self):
        return ntpath.dirname(self.filepath)

    def get_filename(self):
        return ntpath.basename(self.filepath)

    # Rename new mail based on size, for new mail only, append :2,
    def rename_file_based_on_size(self):
        filepath = self.filepath

        try:
            LF = b"\n"
            CRLF = b"\r\n"

            W_size = -1
            with open(filepath, "rb") as f:
                content = f.read()
                content = content.replace(LF, CRLF)
                W_size = len(content)

            dir = ntpath.dirname(filepath)
            filename = ntpath.basename(filepath)
            new_file_size = os.stat(filepath).st_size
            new_filename = re.sub(
                r",S=[0-9]*,W=[0-9]*", f",S={new_file_size},W={W_size}", filename
            )

            pattern = r".*?W=[0-9]*:2,"
            match = re.match(pattern, filename)
            ## New mail
            if match is None:
                new_filename += ":2,"

            new_filepath = os.path.join(dir, new_filename)
            os.rename(filepath, new_filepath)
            return new_filepath

        except Exception as e:
            logger.error(e)

        return filepath

    """
    Don't use re.sub() because special characters have to be escaped in regex.
    """

    def string_without_banners_of(self, content, banner):
        if isinstance(banner, list):
            new_content = content
            for b in banner:
                new_content = new_content.replace(b, "")
            return new_content

        else:
            return content.replace(banner, "")

    """
    (a) Has subject without utf-8 characters
    (b) Has subject with utf-8 characters
    (c) No subject
    """

    def add_subject_banner(self, banner):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                msg = email.message_from_file(f)

                parser = email.parser.HeaderParser()
                headers = parser.parsestr(msg.as_string())
                subject = headers["Subject"]

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                if subject:
                    qp_pattern = r"=\?(?:UTF-8\?Q|utf-8\?q)\?(.*?)\?="
                    b64_pattern = r"=\?(?:UTF-8\?B|utf-8\?b)\?(.*?)\?="
                    qp_match = re.match(qp_pattern, subject)
                    b64_match = re.match(b64_pattern, subject)

                    # (b) Has subject with utf-8 characters + Is quoted-printable
                    if qp_match:
                        content = qp_match.groups()[0]
                        decoded = quopri.decodestring(content, header=True).decode(
                            "utf-8"
                        )

                        #### THIS IS TRICKY that "=\n" is unexpectedly added and corrupts the string.
                        #### Therefore, it has to be removed.
                        encoded = (
                            quopri.encodestring(
                                (
                                    banner
                                    + self.string_without_banners_of(decoded, banner)
                                ).encode("utf-8"),
                                header=True,
                            )
                            .decode("utf-8")
                            .replace("=\n", "")
                        )
                        new_subject = f"=?utf-8?q?{encoded}?="

                        #### Make changes to the file
                        headers.replace_header("Subject", new_subject)
                        f.seek(0)
                        f.write(headers.as_string())
                        f.truncate()

                    # (b) Has subject with utf-8 characters + Is base64
                    elif b64_match:
                        content = b64_match.groups()[0]
                        decoded = base64.b64decode(content).decode("utf-8")

                        new_decoded = banner + self.string_without_banners_of(
                            decoded, banner
                        )
                        if new_decoded != decoded:
                            encoded = (
                                quopri.encodestring(
                                    new_decoded.encode("utf-8"), header=True
                                )
                                .decode("utf-8")
                                .replace("=\n", "")
                            )
                            new_subject = f"=?utf-8?q?{encoded}?="

                            #### Make changes to the file
                            headers.replace_header("Subject", new_subject)
                            f.seek(0)
                            f.write(headers.as_string())
                            f.truncate()

                    # (a) Has subject without utf-8 characters
                    else:
                        if subject.startswith(banner):
                            pass

                        else:
                            new_subject = f"{banner}{subject}"

                            #### Make changes to the file
                            headers.replace_header("Subject", new_subject)
                            f.seek(0)
                            f.write(headers.as_string())
                            f.truncate()

                # (c) No subject
                else:
                    #### Make changes to the file
                    headers.add_header("Subject", banner)
                    f.seek(0)
                    f.write(headers.as_string())
                    f.truncate()

            new_filepath = self.rename_file_based_on_size()

            self.filepath = new_filepath
            return self

        except Exception as e:
            logger.error(e)

        return self

    def remove_subject_banner_if_exists(self, banner):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                msg = email.message_from_file(f)

                parser = email.parser.HeaderParser()
                headers = parser.parsestr(msg.as_string())
                subject = headers["Subject"]

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                if subject:
                    qp_pattern = r"=\?(?:UTF-8\?Q|utf-8\?q)\?(.*?)\?="
                    b64_pattern = r"=\?(?:UTF-8\?B|utf-8\?b)\?(.*?)\?="
                    qp_match = re.match(qp_pattern, subject)
                    b64_match = re.match(b64_pattern, subject)

                    # (b) Has subject with utf-8 characters + Is quoted-printable
                    if qp_match:
                        content = qp_match.groups()[0]
                        #### THIS IS TRICKY that "=\n" is unexpectedly added and corrupts the string.
                        #### Therefore, it has to be removed.
                        decoded = quopri.decodestring(content, header=True).decode(
                            "utf-8"
                        )

                        encoded = (
                            quopri.encodestring(
                                self.string_without_banners_of(decoded, banner).encode(
                                    "utf-8"
                                ),
                                header=True,
                            )
                            .decode("utf-8")
                            .replace("=\n", "")
                        )
                        new_subject = f"=?utf-8?q?{encoded}?="

                        #### Make changes to the file
                        headers.replace_header("Subject", new_subject)
                        f.seek(0)
                        f.write(headers.as_string())
                        f.truncate()

                    # (b) Has subject with utf-8 characters + Is base64
                    elif b64_match:
                        content = b64_match.groups()[0]
                        decoded = base64.b64decode(content).decode("utf-8")

                        new_decoded = self.string_without_banners_of(decoded, banner)
                        if new_decoded != decoded:
                            encoded = (
                                quopri.encodestring(
                                    new_decoded.encode("utf-8"), header=True
                                )
                                .decode("utf-8")
                                .replace("=\n", "")
                            )
                            new_subject = f"=?utf-8?q?{encoded}?="

                            #### Make changes to the file
                            headers.replace_header("Subject", new_subject)
                            f.seek(0)
                            f.write(headers.as_string())
                            f.truncate()

                    # (a) Has subject without utf-8 characters
                    else:
                        new_subject = self.string_without_banners_of(subject, banner)

                        #### Make changes to the file
                        headers.replace_header("Subject", new_subject)
                        f.seek(0)
                        f.write(headers.as_string())
                        f.truncate()

                # (c) No subject
                else:
                    pass

            new_filepath = self.rename_file_based_on_size()

            self.filepath = new_filepath
            return self

        except Exception as e:
            logger.error(e)

        return self

    """
    Define remove_banners_if_exist and add_banners in superclass so that
    error will not be thrown when subclasses that don't need
    this function call this function.
    """

    def remove_banners_if_exist(self, banner_plain_text, banner_html):
        return self

    def add_banners(self, banner_plain_text, banner_html):
        return self

    def remove_all_banners(self):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                msg = email.message_from_file(f)

                parser = email.parser.HeaderParser()
                headers = parser.parsestr(msg.as_string())
                subject = headers["Subject"]

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                if subject:
                    qp_pattern = r"=\?(?:UTF-8\?Q|utf-8\?q)\?(.*?)\?="
                    b64_pattern = r"=\?(?:UTF-8\?B|utf-8\?b)\?(.*?)\?="
                    qp_match = re.match(qp_pattern, subject)
                    b64_match = re.match(b64_pattern, subject)

                    # (b) Has subject with utf-8 characters + Is quoted-printable
                    if qp_match:
                        content = qp_match.groups()[0]
                        #### THIS IS TRICKY that "=\n" is unexpectedly added and corrupts the string.
                        #### Therefore, it has to be removed.
                        decoded = quopri.decodestring(content, header=True).decode(
                            "utf-8"
                        )

                        encoded = (
                            quopri.encodestring(
                                self.string_without_banners_of(
                                    decoded,
                                    [
                                        OLD_UNKNOWN_SUBJECT_BANNER,
                                        OLD_JUNK_SUBJECT_BANNER,
                                        UNKNOWN_SUBJECT_BANNER,
                                        JUNK_SUBJECT_BANNER,
                                    ],
                                ).encode("utf-8"),
                                header=True,
                            )
                            .decode("utf-8")
                            .replace("=\n", "")
                        )
                        new_subject = f"=?utf-8?q?{encoded}?="

                        #### Make changes to the file
                        headers.replace_header("Subject", new_subject)
                        f.seek(0)
                        f.write(headers.as_string())
                        f.truncate()

                    # (b) Has subject with utf-8 characters + Is base64
                    elif b64_match:
                        content = b64_match.groups()[0]
                        decoded = base64.b64decode(content).decode("utf-8")

                        new_decoded = self.string_without_banners_of(
                            decoded,
                            [
                                OLD_UNKNOWN_SUBJECT_BANNER,
                                OLD_JUNK_SUBJECT_BANNER,
                                UNKNOWN_SUBJECT_BANNER,
                                JUNK_SUBJECT_BANNER,
                            ],
                        )
                        if new_decoded != decoded:
                            encoded = (
                                quopri.encodestring(
                                    new_decoded.encode("utf-8"), header=True
                                )
                                .decode("utf-8")
                                .replace("=\n", "")
                            )
                            new_subject = f"=?utf-8?q?{encoded}?="

                            #### Make changes to the file
                            headers.replace_header("Subject", new_subject)
                            f.seek(0)
                            f.write(headers.as_string())
                            f.truncate()

                    # (a) Has subject without utf-8 characters
                    else:
                        new_subject = self.string_without_banners_of(
                            subject,
                            [
                                OLD_UNKNOWN_SUBJECT_BANNER,
                                OLD_JUNK_SUBJECT_BANNER,
                                UNKNOWN_SUBJECT_BANNER,
                                JUNK_SUBJECT_BANNER,
                            ],
                        )

                        #### Make changes to the file
                        headers.replace_header("Subject", new_subject)
                        f.seek(0)
                        f.write(headers.as_string())
                        f.truncate()

                # (c) No subject
                else:
                    pass

            new_filepath = self.rename_file_based_on_size()

            self.filepath = new_filepath

            """
            Remove banners from body
            """
            mutable_email = self.remove_banners_if_exist(
                [
                    OLD_UNKNOWN_BANNER_PLAIN_TEXT,
                    OLD_JUNK_BANNER_PLAIN_TEXT,
                    UNKNOWN_BANNER_PLAIN_TEXT,
                    JUNK_BANNER_PLAIN_TEXT,
                ],
                [
                    OLD_UNKNOWN_BANNER_HTML,
                    OLD_JUNK_BANNER_HTML,
                    UNKNOWN_BANNER_HTML,
                    JUNK_BANNER_HTML,
                ],
            )

            return mutable_email

        except Exception as e:
            logger.error(e)

        return self


"""
(a) Plain text body + (a) No attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("text/plain", "us-ascii", None)
"""


class MutableEmailAA(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                for part in msg.walk():
                    assert part.get_content_type() == "text/plain"

                    ## Have to rely on the decode=True optional flag of get_payload().
                    if (
                        part["Content-Transfer-Encoding"] == "quoted-printable"
                        or part["Content-Transfer-Encoding"] == "base64"
                    ):
                        content = part.get_payload(decode=True).decode("utf-8")
                    else:
                        content = part.get_payload()

                    charset = part.get_content_charset()

                    new_msg.attach(
                        MIMEText(
                            banner_plain_text
                            + self.string_without_banners_of(
                                content, banner_plain_text
                            ),
                            "plain",
                            charset,
                        )
                    )
                    new_msg.attach(
                        MIMEText(
                            banner_html
                            + self.wrap_text_with_default_html(
                                self.string_without_banners_of(content, banner_html)
                            ),
                            "html",
                            charset,
                        )
                    )

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(b) Empty plain text body + (a) No attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("text/plain", None, None)
"""


class MutableEmailBA(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                for part in msg.walk():
                    assert part.get_content_type() == "text/plain"

                    ## Have to rely on the decode=True optional flag of get_payload().
                    if (
                        part["Content-Transfer-Encoding"] == "quoted-printable"
                        or part["Content-Transfer-Encoding"] == "base64"
                    ):
                        content = part.get_payload(decode=True).decode("utf-8")
                    else:
                        content = part.get_payload()

                    assert content == ""

                    new_msg.attach(
                        MIMEText(
                            banner_plain_text,
                            "plain",
                        )
                    )
                    new_msg.attach(
                        MIMEText(
                            banner_html + self.default_html,
                            "html",
                        )
                    )

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(c) Html text body without inline image(s) + (a) No attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/alternative", None, None)
("text/plain", "us-ascii", None)
("text/html", "utf-8", None)
"""


class MutableEmailCA(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                for part in msg.walk():
                    if part.get_content_maintype() == "text":
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            charset = part.get_content_charset()

                            #### quoted-printable -> bytes in that charset -> string
                            content = part.get_payload(decode=True).decode(charset)

                            #### bytes in utf-8
                            encoded_as_bytes = banner_html.encode(
                                "utf-8"
                            ) + self.string_without_banners_of(
                                content, banner_html
                            ).encode(
                                "utf-8"
                            )

                            new_content = encoded_as_bytes.decode("utf-8")

                            if part.get_content_subtype() == "plain":
                                new_msg.attach(
                                    MIMEText(
                                        new_content,
                                        "plain",
                                    )
                                )

                            elif part.get_content_subtype() == "html":
                                new_msg.attach(
                                    MIMEText(
                                        new_content,
                                        "html",
                                    )
                                )

                        else:
                            content = part.get_payload()

                            if part.get_content_subtype() == "plain":
                                new_msg.attach(
                                    MIMEText(
                                        banner_plain_text
                                        + self.string_without_banners_of(
                                            content, banner_plain_text
                                        ),
                                        "plain",
                                    )
                                )

                            elif part.get_content_subtype() == "html":
                                new_msg.attach(
                                    MIMEText(
                                        banner_html
                                        + self.string_without_banners_of(
                                            content, banner_html
                                        ),
                                        "html",
                                    )
                                )

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self

    def remove_banners_if_exist(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                for part in msg.walk():
                    if part.get_content_maintype() == "text":
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        if part.get_content_subtype() == "plain":
                            new_msg.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_plain_text
                                    ),
                                    "plain",
                                )
                            )

                        elif part.get_content_subtype() == "html":
                            new_msg.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_html
                                    ),
                                    "html",
                                )
                            )

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(d) Empty html body + (a) No attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("text/html", "utf-8", None)
"""


class MutableEmailDA(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                for part in msg.walk():
                    assert part.get_content_type() == "text/html"

                    new_msg.attach(
                        MIMEText(
                            banner_plain_text,
                            "plain",
                        )
                    )
                    #### To make the mails consistent, I use the self.default_html
                    # and neglect the current default html.
                    new_msg.attach(
                        MIMEText(
                            banner_html + self.default_html,
                            "html",
                        )
                    )

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(e) Html text body with inline image(s) + (a) No attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/alternative", None, None)
("text/plain", "us-ascii", None)
("multipart/related", None, None)
("text/html", "utf-8", None)
("image/jpeg", None, "inline")
("image/png", None, "inline")
"""


class MutableEmailEA(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                related = None
                for part in msg.walk():
                    if part.get_content_maintype() == "text":
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        if part.get_content_subtype() == "plain":
                            new_msg.attach(
                                MIMEText(
                                    banner_plain_text
                                    + self.string_without_banners_of(
                                        content, banner_plain_text
                                    ),
                                    "plain",
                                )
                            )

                        elif part.get_content_subtype() == "html":
                            related = MIMEMultipart("related")
                            related.attach(
                                MIMEText(
                                    banner_html
                                    + self.string_without_banners_of(
                                        content, banner_html
                                    ),
                                    "html",
                                )
                            )

                    elif part.get_content_disposition() == "inline":
                        assert related != None
                        related.attach(part)

                assert related != None
                new_msg.attach(related)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailEA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self

    def remove_banners_if_exist(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                related = None
                for part in msg.walk():
                    if part.get_content_maintype() == "text":
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        if part.get_content_subtype() == "plain":
                            new_msg.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_plain_text
                                    ),
                                    "plain",
                                )
                            )

                        elif part.get_content_subtype() == "html":
                            related = MIMEMultipart("related")
                            related.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_html
                                    ),
                                    "html",
                                )
                            )

                    elif part.get_content_disposition() == "inline":
                        assert related != None
                        related.attach(part)

                assert related != None
                new_msg.attach(related)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailEA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(f) Only inline image(s) + (a) No attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/related", None, None)
("text/html", "utf-8", None)
("image/jpeg", None, "inline")
("image/png", None, "inline")
"""


class MutableEmailFA(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

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

                new_msg.attach(
                    MIMEText(
                        banner_plain_text,
                        "plain",
                    )
                )
                related = None
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        related = MIMEMultipart("related")
                        related.attach(
                            MIMEText(
                                banner_html
                                + self.string_without_banners_of(content, banner_html),
                                "html",
                            )
                        )

                    elif part.get_content_disposition() == "inline":
                        assert related != None
                        related.attach(part)

                assert related != None
                new_msg.attach(related)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailEA(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


##########################################################
##########################################################
##########################################################
#### With attachment below ####
##########################################################
##########################################################
##########################################################

"""
(a) Plain text body + (b) Has attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/mixed", None, None)
("text/plain", "us-ascii", None)
("text/plain", None, "attachment")
("application/pdf", None, "attachment")
("image/jpeg", None, "attachment")
"""


class MutableEmailAB(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")
                alternative = MIMEMultipart("alternative")
                is_alternative_attached = False

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

                for part in msg.walk():
                    if (
                        part.get_content_type() == "text/plain"
                        and part.get_content_disposition() != "attachment"
                    ):
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        alternative.attach(
                            MIMEText(
                                banner_plain_text
                                + self.string_without_banners_of(
                                    content, banner_plain_text
                                ),
                                "plain",
                            )
                        )
                        alternative.attach(
                            MIMEText(
                                banner_html
                                + self.wrap_text_with_default_html(
                                    self.string_without_banners_of(content, banner_html)
                                ),
                                "html",
                            )
                        )
                    elif part.get_content_disposition() == "attachment":
                        if not is_alternative_attached:
                            is_alternative_attached = True
                            new_msg.attach(alternative)

                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(b) Empty plain text body + (b) Has attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/mixed", None, None)
("text/plain", None, "attachment")
("application/pdf", None, "attachment")
("image/jpeg", None, "attachment")
"""


class MutableEmailBB(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")

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

                alternative = MIMEMultipart("alternative")
                alternative.attach(
                    MIMEText(
                        banner_plain_text,
                        "plain",
                    )
                )
                alternative.attach(
                    MIMEText(
                        banner_html + self.default_html,
                        "html",
                    )
                )
                new_msg.attach(alternative)

                for part in msg.walk():
                    if part.get_content_disposition() == "attachment":
                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(c) Html text body without inline image(s) + (b) Has attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/mixed", None, None)
("multipart/alternative", None, None)
("text/plain", "us-ascii", None)
("text/html", "utf-8", None)
("text/plain", None, "attachment")
("application/pdf", None, "attachment")
("image/jpeg", None, "attachment")
"""


class MutableEmailCB(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")
                alternative = MIMEMultipart("alternative")
                is_alternative_attached = False

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

                for part in msg.walk():
                    if (
                        part.get_content_maintype() == "text"
                        and part.get_content_disposition() != "attachment"
                    ):
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        if part.get_content_subtype() == "plain":
                            alternative.attach(
                                MIMEText(
                                    banner_plain_text
                                    + self.string_without_banners_of(
                                        content, banner_plain_text
                                    ),
                                    "plain",
                                )
                            )

                        elif part.get_content_subtype() == "html":
                            alternative.attach(
                                MIMEText(
                                    banner_html
                                    + self.string_without_banners_of(
                                        content, banner_html
                                    ),
                                    "html",
                                )
                            )

                    elif part.get_content_disposition() == "attachment":
                        if not is_alternative_attached:
                            is_alternative_attached = True
                            new_msg.attach(alternative)

                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self

    def remove_banners_if_exist(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")
                alternative = MIMEMultipart("alternative")
                is_alternative_attached = False

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

                for part in msg.walk():
                    if (
                        part.get_content_maintype() == "text"
                        and part.get_content_disposition() != "attachment"
                    ):
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        if part.get_content_subtype() == "plain":
                            alternative.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_plain_text
                                    ),
                                    "plain",
                                )
                            )

                        elif part.get_content_subtype() == "html":
                            alternative.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_html
                                    ),
                                    "html",
                                )
                            )

                    elif part.get_content_disposition() == "attachment":
                        if not is_alternative_attached:
                            is_alternative_attached = True
                            new_msg.attach(alternative)

                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(d) Empty html body + (b) Has attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/mixed", None, None)
("text/html", "utf-8", None)
("text/plain", None, "attachment")
("application/pdf", None, "attachment")
("image/jpeg", None, "attachment")
"""


class MutableEmailDB(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")
                alternative = MIMEMultipart("alternative")
                is_alternative_attached = False

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

                for part in msg.walk():
                    if (
                        part.get_content_type() == "text/html"
                        and part.get_content_disposition() != "attachment"
                    ):
                        alternative.attach(
                            MIMEText(
                                banner_plain_text,
                                "plain",
                            )
                        )
                        #### To make the mails consistent, I use the self.default_html
                        # and neglect the current default html.
                        alternative.attach(
                            MIMEText(
                                banner_html + self.default_html,
                                "html",
                            )
                        )

                    elif part.get_content_disposition() == "attachment":
                        if not is_alternative_attached:
                            is_alternative_attached = True
                            new_msg.attach(alternative)

                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailCB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(e) Html text body with inline image(s) + (b) Has attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/mixed", None, None)
("multipart/alternative", None, None)
("text/plain", "us-ascii", None)
("multipart/related", None, None)
("text/html", "utf-8", None)
("image/jpeg", None, "inline")
("image/png", None, "inline")
("text/plain", None, "attachment")
("application/pdf", None, "attachment")
("image/jpeg", None, "attachment")
"""


class MutableEmailEB(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")
                alternative = MIMEMultipart("alternative")
                is_alternative_attached = False

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

                related = None
                for part in msg.walk():
                    if (
                        part.get_content_maintype() == "text"
                        and part.get_content_disposition() != "attachment"
                    ):
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        if part.get_content_subtype() == "plain":
                            alternative.attach(
                                MIMEText(
                                    banner_plain_text
                                    + self.string_without_banners_of(
                                        content, banner_plain_text
                                    ),
                                    "plain",
                                )
                            )

                        elif (
                            part.get_content_subtype() == "html"
                            and part.get_content_disposition() != "attachment"
                        ):
                            related = MIMEMultipart("related")
                            related.attach(
                                MIMEText(
                                    banner_html
                                    + self.string_without_banners_of(
                                        content, banner_html
                                    ),
                                    "html",
                                )
                            )

                    elif part.get_content_disposition() == "inline":
                        assert related != None
                        related.attach(part)

                    elif part.get_content_disposition() == "attachment":
                        if not is_alternative_attached:
                            is_alternative_attached = True

                            assert related != None
                            alternative.attach(related)
                            new_msg.attach(alternative)

                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailEB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self

    def remove_banners_if_exist(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")
                alternative = MIMEMultipart("alternative")
                is_alternative_attached = False

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

                related = None
                for part in msg.walk():
                    if (
                        part.get_content_maintype() == "text"
                        and part.get_content_disposition() != "attachment"
                    ):
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        if part.get_content_subtype() == "plain":
                            alternative.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_plain_text
                                    ),
                                    "plain",
                                )
                            )

                        elif (
                            part.get_content_subtype() == "html"
                            and part.get_content_disposition() != "attachment"
                        ):
                            related = MIMEMultipart("related")
                            related.attach(
                                MIMEText(
                                    self.string_without_banners_of(
                                        content, banner_html
                                    ),
                                    "html",
                                )
                            )

                    elif part.get_content_disposition() == "inline":
                        assert related != None
                        related.attach(part)

                    elif part.get_content_disposition() == "attachment":
                        if not is_alternative_attached:
                            is_alternative_attached = True

                            assert related != None
                            alternative.attach(related)
                            new_msg.attach(alternative)

                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailEB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


"""
(f) Only inline image(s) + (b) Has attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/mixed", None, None)
("multipart/related", None, None)
("text/html", "utf-8", None)
("image/jpeg", None, "inline")
("image/png", None, "inline")
("text/plain", None, "attachment")
("application/pdf", None, "attachment")
("image/jpeg", None, "attachment")
"""


class MutableEmailFB(MutableEmail):
    def add_banners(self, banner_plain_text, banner_html):
        filepath = self.filepath

        try:
            with open(filepath, "r+") as f:
                # Use policy=policy.default so that this returns an EmailMessage object instead of Message object.
                # Whole email message including both headers and content.
                msg = email.message_from_file(f, policy=policy.default)

                new_msg = MIMEMultipart("mixed")
                alternative = MIMEMultipart("alternative")
                is_alternative_attached = False

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

                alternative.attach(
                    MIMEText(
                        banner_plain_text,
                        "plain",
                    )
                )
                related = None
                for part in msg.walk():
                    if (
                        part.get_content_type() == "text/html"
                        and part.get_content_disposition() != "attachment"
                    ):
                        ## Have to rely on the decode=True optional flag of get_payload().
                        if (
                            part["Content-Transfer-Encoding"] == "quoted-printable"
                            or part["Content-Transfer-Encoding"] == "base64"
                        ):
                            content = part.get_payload(decode=True).decode("utf-8")
                        else:
                            content = part.get_payload()

                        related = MIMEMultipart("related")
                        related.attach(
                            MIMEText(
                                banner_html
                                + self.string_without_banners_of(content, banner_html),
                                "html",
                            )
                        )

                    elif part.get_content_disposition() == "inline":
                        assert related != None
                        related.attach(part)

                    elif part.get_content_disposition() == "attachment":
                        if not is_alternative_attached:
                            is_alternative_attached = True

                            assert related != None
                            alternative.attach(related)
                            new_msg.attach(alternative)

                        new_msg.attach(part)

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                # dir = ntpath.dirname(ntpath.dirname(filepath))
                # filename = ntpath.basename(filepath)
                # backup_dir = os.path.join(dir, "backup")
                # backup_filepath = os.path.join(backup_dir, filename)
                # Path(backup_dir).mkdir(exist_ok=True)
                # copyfile(filepath, backup_filepath)
                #### Testing only END ####
                ######################

                f.seek(0)
                f.write(new_msg.as_string())
                f.truncate()

            new_filepath = self.rename_file_based_on_size()

            return MutableEmailEB(new_filepath)

        except Exception as e:
            logger.error(e)

        return self


# filepath = "/mailu/mail/cs@michaelfong.co/cur/1636819751.M553581P2086.f9db57f63506,S=2896,W=947:2,S"
# mutable_email = MutableEmailFactory.create_mutable_email(filepath)
# print(type(mutable_email))

# mutable_email = mutable_email.add_banners(
#     UNKNOWN_BANNER_PLAIN_TEXT, UNKNOWN_BANNER_HTML
# )
# print(type(mutable_email))
# print(mutable_email.filepath)

# mutable_email = mutable_email.remove_banners_if_exist(
#     OLD_UNKNOWN_BANNER_PLAIN_TEXT, OLD_UNKNOWN_BANNER_HTML
# )
# print(type(mutable_email))
# print(mutable_email.filepath)

# mutable_email = mutable_email.add_subject_banner(UNKNOWN_SUBJECT_BANNER)
# print(type(mutable_email))
# print(mutable_email.filepath)

# mutable_email = mutable_email.remove_subject_banner_if_exists(UNKNOWN_SUBJECT_BANNER)
# print(type(mutable_email))
# print(mutable_email.filepath)

filepath = "/mailu/mail/pc@michaelfong.co/cur/1638100587.M305640P8061.f9db57f63506,S=1502,W=1538:2,S"
mutable_email = MutableEmailFactory.create_mutable_email(filepath)
mutable_email = mutable_email.add_banners(
    UNKNOWN_BANNER_PLAIN_TEXT, UNKNOWN_BANNER_HTML
)
# mutable_email.rename_file_based_on_size()
print(mutable_email)


# filepath = "/mailu/mail/pc@michaelfong.co/cur/1638116225.M828741P14295.f9db57f63506,S=1477,W=1513:2,S"
# mutable_email = MutableEmailFactory.create_mutable_email(filepath)
# # mutable_email.rename_file_based_on_size()
# mutable_email = mutable_email.add_banners(
#     UNKNOWN_BANNER_PLAIN_TEXT, UNKNOWN_BANNER_HTML
# )
# print(mutable_email)
# %%
