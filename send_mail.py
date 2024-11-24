from config import Config
import smtplib
from email.mime.text import MIMEText

def send_email(to_email: str, subject: str, message: str):
    msg = MIMEText(message, "plain")
    msg["Subject"] = subject
    msg["From"] = Config.SENDER_MAIL
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(Config.SENDER_MAIL, Config.SENDER_PASS)
        server.sendmail(Config.SENDER_MAIL, to_email, msg.as_string())