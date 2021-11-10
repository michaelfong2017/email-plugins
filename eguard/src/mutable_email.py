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

logger = logging.getLogger()

OLD_UNKNOWN_BANNER_PLAIN_TEXT = """注意：
這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
CAUTION: 
The domain of email sender is first seen.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""
OLD_UNKNOWN_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff7400; padding: 5px;"><span>注意：<br />這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />CAUTION:<br/>The domain of email sender is first seen. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""

UNKNOWN_BANNER_PLAIN_TEXT = """注意：
這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。
CAUTION: 
The domain of email sender is first seen.  Beware of any
hyperlink, attachment and bank account information unless you ensure the
authenticity of the sender.  Seek IT assistance if in doubt.  

"""
UNKNOWN_BANNER_HTML = """<p style="margin: 10px 20%; text-align: center; border: 2px solid; background-color: #ff7400; padding: 5px;"><span>注意：<br />這是首次接收到的電郵地址。除非您確保其真確性，否則請留意當中所附有的超連結，附件或銀行帳戶資料。如有疑問，請尋求技術人員的支援。</span><br />CAUTION:<br/>The domain of email sender is first seen. &nbsp;Beware of any hyperlink, attachment and bank account information unless you ensure the authenticity of the sender. &nbsp;Seek IT assistance if in doubt.&nbsp;&nbsp;</p>\n"""


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
                                and part.get_content_charset() is None
                            ):
                                return MutableEmailBB(filepath)
                            elif (
                                part.get_content_type() == "text/plain"
                                and part.get_content_charset() is not None
                            ):
                                return MutableEmailAB(filepath)
                            elif part.get_content_type() == "multipart/alternative":
                                has_alternative = True
                                continue
                            else:
                                logger.error("Unexpected structure!")
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

        return MutableEmailAA(filepath)


class MutableEmail:
    default_html = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head><body style='font-size: 10pt; font-family: Verdana,Geneva,sans-serif'>

</body></html>"""

    def wrap_text_with_default_html(self, text):
        return f"""<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head><body style='font-size: 10pt; font-family: Verdana,Geneva,sans-serif'>
<div>
<div><span>{text}</span></div>
</body></html>"""

    def __init__(self, filepath):
        self.filepath = filepath

    # Rename file based on size
    def rename_file_based_on_size(self):
        filepath = self.filepath

        try:
            dir = ntpath.dirname(filepath)
            filename = ntpath.basename(filepath)
            new_file_size = os.stat(filepath).st_size
            new_filename = re.sub(r",S=[0-9]*,", f",S={new_file_size},", filename)
            new_filepath = os.path.join(dir, new_filename)
            os.rename(filepath, new_filepath)
            return new_filepath

        except Exception as e:
            logger.error(e)

        return filepath

    def string_without_banneer_of(self, content, banner):
        return re.sub(banner, "", content)


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
                    content = part.get_payload(decode=True).decode("utf-8")
                    new_msg.attach(
                        MIMEText(
                            banner_plain_text
                            + self.string_without_banneer_of(
                                content, banner_plain_text
                            ),
                            "plain",
                        )
                    )
                    new_msg.attach(
                        MIMEText(
                            banner_html
                            + self.wrap_text_with_default_html(
                                self.string_without_banneer_of(content, banner_html)
                            ),
                            "html",
                        )
                    )

                #### Testing only ####
                ######################
                # print(new_msg.as_string())
                dir = ntpath.dirname(ntpath.dirname(filepath))
                filename = ntpath.basename(filepath)
                backup_dir = os.path.join(dir, "backup")
                backup_filepath = os.path.join(backup_dir, filename)
                Path(backup_dir).mkdir(exist_ok=True)
                copyfile(filepath, backup_filepath)
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
                    content = part.get_payload(decode=True).decode("utf-8")
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
                dir = ntpath.dirname(ntpath.dirname(filepath))
                filename = ntpath.basename(filepath)
                backup_dir = os.path.join(dir, "backup")
                backup_filepath = os.path.join(backup_dir, filename)
                Path(backup_dir).mkdir(exist_ok=True)
                copyfile(filepath, backup_filepath)
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
                    content = part.get_payload(decode=True).decode("utf-8")
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
                dir = ntpath.dirname(ntpath.dirname(filepath))
                filename = ntpath.basename(filepath)
                backup_dir = os.path.join(dir, "backup")
                backup_filepath = os.path.join(backup_dir, filename)
                Path(backup_dir).mkdir(exist_ok=True)
                copyfile(filepath, backup_filepath)
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
                    content = part.get_payload(decode=True).decode("utf-8")
                    if part.get_content_subtype() == "plain":
                        new_msg.attach(
                            MIMEText(
                                self.string_without_banneer_of(
                                    content, banner_plain_text
                                ),
                                "plain",
                            )
                        )

                    elif part.get_content_subtype() == "html":
                        new_msg.attach(
                            MIMEText(
                                self.string_without_banneer_of(content, banner_html),
                                "html",
                            )
                        )

            #### Testing only ####
            ######################
            # print(new_msg.as_string())
            dir = ntpath.dirname(ntpath.dirname(filepath))
            filename = ntpath.basename(filepath)
            backup_dir = os.path.join(dir, "backup")
            backup_filepath = os.path.join(backup_dir, filename)
            Path(backup_dir).mkdir(exist_ok=True)
            copyfile(filepath, backup_filepath)
            #### Testing only END ####
            ######################

            f.seek(0)
            f.write(new_msg.as_string())
            f.truncate()

        new_filepath = self.rename_file_based_on_size()

        return MutableEmailCA(new_filepath)


class MutableEmailDA(MutableEmail):
    pass


class MutableEmailEA(MutableEmail):
    pass


class MutableEmailFA(MutableEmail):
    pass


class MutableEmailAB(MutableEmail):
    pass


class MutableEmailBB(MutableEmail):
    pass


class MutableEmailCB(MutableEmail):
    pass


class MutableEmailDB(MutableEmail):
    pass


class MutableEmailEB(MutableEmail):
    pass


class MutableEmailFB(MutableEmail):
    pass


filepath = "/mailu/mail/cs@michaelfong.co/cur/1636096711.M127784P6455.f9db57f63506,S=1579,W=1621:2,S"
mutable_email = MutableEmailFactory.create_mutable_email(filepath)
print(type(mutable_email))
mutable_email = mutable_email.add_banners(
    UNKNOWN_BANNER_PLAIN_TEXT, UNKNOWN_BANNER_HTML
)
print(type(mutable_email))
mutable_email = mutable_email.remove_banners_if_exist(
    OLD_UNKNOWN_BANNER_PLAIN_TEXT, OLD_UNKNOWN_BANNER_HTML
)
print(type(mutable_email))


# %%
