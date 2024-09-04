import imaplib
import smtplib
from email import message_from_bytes
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import formataddr
from config import Config
from models import ProcessedEmail
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Инициализация базы данных
engine = create_engine('sqlite:///emails.db')
Session = sessionmaker(bind=engine)
session = Session()

def connect_to_email():
    mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER)
    mail.login(Config.EMAIL_ACCOUNT, Config.PASSWORD)
    mail.select("inbox")
    return mail

def decode_mime_words(s):
    return ''.join(
        word.decode(encoding or 'utf-8') if isinstance(word, bytes) else word
        for word, encoding in decode_header(s)
    )

def fetch_emails(mail):
    processed_uids = {email.uid for email in session.query(ProcessedEmail).all()}
    status, messages = mail.uid('search', None, "ALL")
    email_uids = messages[0].split()

    emails = []
    for uid in email_uids:
        uid_str = uid.decode('utf-8')
        if uid_str not in processed_uids:
            status, msg_data = mail.uid('fetch', uid, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email)

            subject = decode_mime_words(msg["Subject"])
            from_ = decode_mime_words(msg.get("From"))

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            date = msg.get("Date")

            emails.append({
                "uid": uid_str,
                "subject": subject,
                "from": from_,
                "body": body,
                "date": date
            })
    return emails

def save_processed_uid(uid):
    processed_email = ProcessedEmail(uid=uid)
    session.add(processed_email)
    session.commit()

def send_email(subject, body, to_email):
    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Your Service", Config.SEND_FROM_EMAIL))
    msg["To"] = to_email

    with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.EMAIL_ACCOUNT, Config.PASSWORD)
        server.sendmail(Config.SEND_FROM_EMAIL, [to_email], msg.as_string())
    print(f"Result sent to {to_email}")
