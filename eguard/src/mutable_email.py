#%%
import email
from email import policy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ntpath
import os
from pathlib import Path
import re
from shutil import copyfile


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
        return MutableEmailAA(filepath)


class MutableEmail:
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
            pass

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
                        + self.string_without_banneer_of(content, banner_plain_text),
                        "plain",
                    )
                )
                new_msg.attach(
                    MIMEText(
                        banner_html
                        + self.string_without_banneer_of(content, banner_html),
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


"""
(c) Html text body without inline image(s) + (a) No attachment(s)
(Content-Type, charset, Content-Disposition) are as follows:
("multipart/alternative", None, None)
("text/plain", "us-ascii", None)
("text/html", "utf-8", None)
"""


class MutableEmailCA(MutableEmail):
    def add_banners(self):
        print(self.filepath)
        return MutableEmailCA("filepath_CA")

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


# filepath = "/mailu/mail/cs@michaelfong.co/cur/1636137339.M336256P14189.f9db57f63506,S=975,W=1000:2,S"
# mutable_email = MutableEmailFactory.create_mutable_email(filepath)
# print(type(mutable_email))
# mutable_email = mutable_email.add_banners(
#     UNKNOWN_BANNER_PLAIN_TEXT, UNKNOWN_BANNER_HTML
# )
# print(type(mutable_email))
# mutable_email = mutable_email.remove_banners_if_exist(
#     OLD_UNKNOWN_BANNER_PLAIN_TEXT, OLD_UNKNOWN_BANNER_HTML
# )
# print(type(mutable_email))


# %%
