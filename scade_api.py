import requests
import time
import json
from config import Config

def send_to_scade(email_data):
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

    response = requests.post(Config.SCADE_API_URL, headers=headers, data=payload)

    if response.status_code == 200:
        task_id = response.json().get("id")
        return task_id
    else:
        print(f"Failed to start flow. Status code: {response.status_code}, Response: {response.text}")
        return None

def get_scade_result(task_id):
    result_url = f"https://api.scade.pro/api/v1/task/{task_id}"
    headers = {"Authorization": f"Basic {Config.API_TOKEN}"}

    while True:
        response = requests.get(result_url, headers=headers)
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get("status") == 3:
                return result_data
            time.sleep(5)
        else:
            print(f"Failed to get result. Status code: {response.status_code}, Response: {response.text}")
            return None
