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
TO_EMAIL = os.getenv("TO_EMAIL1")

def send_email(subject: str, message: str, file_path: str = None):
    try:
        if not MY_EMAIL or not EMAIL_PASSWORD or not TO_EMAIL:
            return False

        msg = MIMEMultipart()
        msg["From"] = MY_EMAIL
        msg["To"] = TO_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        logging.debug(f"📎 Тема: {subject}")
        logging.debug(f"📎 Сообщение: {message}")

        if file_path:
            logging.info(f"🖼 Попытка прикрепить файл: {file_path}")

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

            logging.info(f"✅ Файл {file_path} успешно прикреплен с MIME-типом {mime_type}.")

        logging.info(f"📡 Подключаемся к SMTP-серверу {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        logging.info("🔒 Соединение зашифровано (STARTTLS включен).")

        logging.info("🔑 Пытаемся войти в Gmail...")
        server.login(MY_EMAIL, EMAIL_PASSWORD)
        logging.info("✅ Авторизация успешна!")

        logging.info("📤 Отправка письма...")
        server.sendmail(MY_EMAIL, TO_EMAIL, msg.as_string())
        server.quit()

        logging.info("✅ Email отправлен успешно!")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка отправки email: {e}")
        return False