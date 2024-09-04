import imaplib
from email import message_from_bytes
from email.header import decode_header
import requests
import time
import json
from config import Config
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


def decode_mime_words(s):
    return ''.join(
        word.decode(encoding or 'utf-8') if isinstance(word, bytes) else word
        for word, encoding in decode_header(s)
    )


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
            msg = message_from_bytes(raw_email)

            # Декодирование заголовков
            subject = decode_mime_words(msg["Subject"])
            from_ = decode_mime_words(msg.get("From"))

            # Извлечение тела письма
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            # Получение даты
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
    # Сохранение UID обработанного письма в базе данных
    processed_email = ProcessedEmail(uid=uid)
    session.add(processed_email)
    session.commit()


def send_to_scade(email_data):
    # Сериализация данных для Scade API
    payload = json.dumps({
        "start_node_id": Config.START_NODE_ID,
        "end_node_id": Config.END_NODE_ID,
        "result_node_id": Config.RESULT_NODE_ID,
        "node_settings": {
            Config.START_NODE_ID: {
                "data": {
                    "from": email_data["from"],
                    "subject": email_data["subject"],
                    "body": email_data["body"],
                    "date": email_data["date"]
                }
            }
        }
    })

    headers = {
        'Authorization': f'Basic {Config.API_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Отправка POST запроса для запуска флоу
    response = requests.post(Config.SCADE_API_URL, headers=headers, data=payload)

    if response.status_code == 200:
        # Возвращаем task_id для последующего запроса
        task_id = response.json().get("id")
        return task_id
    else:
        print(f"Failed to start flow. Status code: {response.status_code}, Response: {response.text}")
        return None


def get_scade_result(task_id):
    # Получение результата выполнения флоу по task_id
    result_url = f"https://api.scade.pro/api/v1/task/{task_id}"
    headers = {
        "Authorization": f"Basic {Config.API_TOKEN}"
    }

    while True:
        response = requests.get(result_url, headers=headers)
        if response.status_code == 200:
            result_data = response.json()
            status = result_data.get("status")

            # Если задача завершена, возвращаем результат
            if status == 3:  # Статус 3 указывает на завершение задачи
                return result_data  # Возвращаем весь результат
            else:
                print(f"Task {task_id} is still running... Waiting for result.")
                time.sleep(5)  # Задержка перед повторным запросом
        else:
            print(f"Failed to get flow result. Status code: {response.status_code}, Response: {response.text}")
            return None


def save_result_to_html(task_id, scade_response):
    # Проверка наличия данных в ответе
    if scade_response is None:
        print(f"No result data found for task ID: {task_id}.")
        return

    # Попытка извлечь данные из 'result'
    result_data = scade_response.get("result", {})

    # Если данных в 'result' нет, пытаемся извлечь из 'node_settings["axi1-start"]'
    if not result_data:
        result_data = scade_response.get("data", {}).get("node_settings", {}).get(Config.START_NODE_ID, {}).get("data", {})

    # Извлекаем значения с использованием метода .get(), чтобы избежать KeyError
    from_ = result_data.get("from", "N/A")
    subject = result_data.get("subject", "N/A")
    body = result_data.get("body", "N/A")
    date = result_data.get("date", "N/A")

    # Создание HTML-контента
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Scade Result - Task ID: {task_id}</title>
    </head>
    <body>
        <h1>Scade Task Result</h1>
        <p><strong>Task ID:</strong> {task_id}</p>
        <p><strong>From:</strong> {from_}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Date:</strong> {date}</p>
        <p><strong>Body:</strong></p>
        <pre>{body}</pre>
    </body>
    </html>
    """

    # Сохранение HTML-файла с кодировкой utf-8
    filename = f"scade_result_{task_id}.html"
    with open(filename, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

    print(f"Result saved to {filename}")

def main():
    mail = connect_to_email()

    while True:
        emails = fetch_emails(mail)
        if emails:
            for email_data in emails:
                task_id = send_to_scade(email_data)
                if task_id:
                    print(f"Email from {email_data['from']} successfully sent to Scade API. Task ID: {task_id}")

                    # Ожидаем завершения флоу и получаем результат
                    scade_response = get_scade_result(task_id)
                    if scade_response:
                        save_result_to_html(task_id, scade_response)

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
