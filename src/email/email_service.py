import smtplib
import os
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes  # Определяет MIME-тип файла автоматически
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MY_EMAIL = os.getenv("MY_EMAIL")
EMAIL_PASSWORD = os.getenv("PASS_EMAIL")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def render_template(template_name: str, context: dict):
    template = env.get_template(template_name)
    return template.render(context)


def send_email(to_email: str, subject: str, message: str, file_path: str = None) -> bool:
    try:
        if not MY_EMAIL or not EMAIL_PASSWORD or not to_email:
            logging.error("❌ Email credentials not set.")
            return False

        msg = MIMEMultipart()
        msg["From"] = MY_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        html = render_template("single_file.html", {
            "subject": subject,
            "message": message,
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        })
        msg.attach(MIMEText(html, "html"))

        if file_path:
            if not os.path.exists(file_path):
                logging.warning(f"⚠️ File not found: {file_path}")
                return False

            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

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

        # os.remove(file_path)
        return True

    except Exception as e:
        logging.error(f"❌ Error sending email: {e}")
        return False


def send_email_with_files(to_email: str, subject: str, message: str, file_paths: list[str]) -> bool:
    try:
        if not MY_EMAIL or not EMAIL_PASSWORD or not to_email:
            logging.error("❌ Email credentials not set.")
            return False

        msg = MIMEMultipart()
        msg["From"] = MY_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        html = render_template("media_group.html", {
            "subject": subject,
            "message": message,
            "files_count": len(file_paths),
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        })
        msg.attach(MIMEText(html, "html"))

        for file_path in file_paths:
            if not os.path.exists(file_path):
                logging.warning(f"⚠️ File not found: {file_path}")
                continue

            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

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

        # for path in file_paths:
        #     try:
        #         os.remove(path)
        #     except Exception as e:
        #         logging.warning(f"⚠️ Failed to delete {path}: {e}")

        return True

    except Exception as e:
        logging.error(f"❌ Error sending email: {e}")
        return False