from email_utils import connect_to_email, fetch_emails, save_processed_uid, send_email
from scade_api import send_to_scade, get_scade_result
from html_utils import save_result_to_html
from config import Config
import time

def main():
    mail = connect_to_email()

    while True:
        emails = fetch_emails(mail)
        if emails:
            for email_data in emails:
                task_id = send_to_scade(email_data)
                if task_id:
                    print(f"Email from {email_data['from']} successfully sent to Scade API. Task ID: {task_id}")
                    scade_response = get_scade_result(task_id)
                    if scade_response:
                        html_content = save_result_to_html(task_id, scade_response)
                        send_email(f"Scade Task Result - Task ID {task_id}", html_content, Config.SEND_TO_EMAIL)
                    save_processed_uid(email_data['uid'])
                else:
                    print(f"Failed to send email from {email_data['from']} to Scade API.")
        else:
            print("No new emails found.")

        time.sleep(Config.CHECK_INTERVAL)

if __name__ == "__main__":
    main()
