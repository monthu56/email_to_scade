import imaplib
from email import message_from_bytes  # Импортируем только необходимую функцию
from email.header import decode_header
import requests
import time
from config import Config
from base64 import b64encode
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import ProcessedEmail

# Инициализация базы данных
engine = create_engine('sqlite:///emails.db')
Session = sessionmaker(bind=engine)
session = Session()


def connect_to_email():
    # Подключение к почтовому серверу
    mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER)
    mail.login(Config.EMAIL_ACCOUNT, Config.PASSWORD)
    mail.select("inbox")
    return mail


def fetch_emails(mail):
    # Получение UID всех уже обработанных писем
    processed_uids = {email.uid for email in session.query(ProcessedEmail).all()}

    # Получение всех новых писем (UID, которых нет в базе данных)
    status, messages = mail.uid('search', None, "ALL")
    email_uids = messages[0].split()

    emails = []

    for uid in email_uids:
        uid_str = uid.decode('utf-8')
        if uid_str not in processed_uids:
            # Получение тела письма
            status, msg_data = mail.uid('fetch', uid, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email)  # Используем явный импорт message_from_bytes

            # Декодирование заголовков
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')

            from_ = msg.get("From")

            # Извлечение тела письма
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            emails.append({
                "uid": uid_str,
                "subject": subject,
                "from": from_,
                "body": body
            })

    return emails


def save_processed_uid(uid):
    # Сохранение UID обработанного письма в базе данных
    processed_email = ProcessedEmail(uid=uid)
    session.add(processed_email)
    session.commit()


def prepare_scade_data(email_data):
    # Преобразование данных письма в формат JSON для Scade
    scade_data = {
        "start_node_id": Config.START_NODE_ID,
        "end_node_id": Config.END_NODE_ID,
        "result_node_id": Config.RESULT_NODE_ID,
        "node_settings": {
            Config.START_NODE_ID: {
                "data": {
                    "subject": email_data["subject"],
                    "from": email_data["from"],
                    "body": email_data["body"]
                }
            }
        }
    }
    return scade_data


def send_to_scade(scade_data):
    # Подготовка заголовков для запроса
    auth_token = b64encode(f"{Config.API_TOKEN}:".encode()).decode("ascii")
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Basic {auth_token}"
    }

    # Отправка данных на Scade API
    response = requests.post(Config.SCADE_API_URL, headers=headers, json=scade_data)
    if response.status_code == 200:
        task_id = response.json().get("id")
        return task_id
    else:
        print(f"Failed to start flow. Status code: {response.status_code}, Response: {response.text}")
        return None


def get_scade_result(task_id):
    # Получение результата выполнения флоу
    result_url = f"https://api.scade.pro/api/v1/task/{task_id}"
    auth_token = b64encode(f"{Config.API_TOKEN}:".encode()).decode("ascii")
    headers = {
        "Authorization": f"Basic {auth_token}"
    }

    response = requests.get(result_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get flow result. Status code: {response.status_code}, Response: {response.text}")
        return None


def save_result_to_file(task_id, result):
    # Сохранение результата в текстовый файл
    filename = f"scade_result_{task_id}.txt"
    with open(filename, 'w') as file:
        file.write(f"Task ID: {task_id}\n")
        file.write(f"Result: {result}\n")
    print(f"Result saved to {filename}")


def main():
    mail = connect_to_email()

    while True:
        emails = fetch_emails(mail)
        if emails:
            for email_data in emails:
                scade_data = prepare_scade_data(email_data)
                task_id = send_to_scade(scade_data)
                if task_id:
                    print(f"Email from {email_data['from']} successfully sent to Scade API. Task ID: {task_id}")

                    # Опционально: ожидаем завершения флоу и получаем результат
                    time.sleep(5)  # Задержка перед запросом результата
                    result = get_scade_result(task_id)
                    if result:
                        save_result_to_file(task_id, result)

                    # Сохранение UID после успешной отправки
                    save_processed_uid(email_data['uid'])
                else:
                    print(f"Failed to send email from {email_data['from']} to Scade API.")
        else:
            print("No new emails found.")

        print("Waiting for new emails...")
        time.sleep(Config.CHECK_INTERVAL)


if __name__ == "__main__":
    main()
