import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes  # Определяет MIME-тип файла автоматически

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MY_EMAIL = os.getenv("MY_EMAIL")
EMAIL_PASSWORD = os.getenv("PASS_EMAIL")


def send_email(to_email: str, subject: str, message: str, file_path: str = None):
    try:
        if not MY_EMAIL or not EMAIL_PASSWORD or not to_email:
            return False

        msg = MIMEMultipart()
        msg["From"] = MY_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))


        if file_path:

            if not os.path.exists(file_path):
                logging.error(f"❌ Файл {file_path} не найден!")
                return False

            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            main_type, sub_type = mime_type.split("/", 1)

            with open(file_path, "rb") as attachment:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(file_path)}"'
            )
            part.add_header("Content-Type", f"{mime_type}; name={os.path.basename(file_path)}")

            msg.attach(part)


        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()

        server.login(MY_EMAIL, EMAIL_PASSWORD)

        server.sendmail(MY_EMAIL, to_email, msg.as_string())
        server.quit()

        # if file_path:
        #     try:
        #         os.remove(file_path)
        #         logging.info(f"🗑 Файл {file_path} удалён после успешной отправки.")
        #     except Exception as e:
        #         logging.error(f"❌ Ошибка удаления файла {file_path}: {e}")

        return True
    except Exception as e:
        return False

def send_email_with_files(to_email: str, subject: str, message: str, file_paths: list[str]):
    try:
        if not MY_EMAIL or not EMAIL_PASSWORD or not to_email:
            return False

        msg = MIMEMultipart()
        msg["From"] = MY_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue

            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)

            with open(file_path, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())

            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
            msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(MY_EMAIL, EMAIL_PASSWORD)
        server.sendmail(MY_EMAIL, to_email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        return False

