import requests
from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

def check_whatsapp_status(message_id):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    url = f"https://graph.facebook.com/v18.0/{message_id}"

    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200:
        print(f"Message Status: {data.get('messages', [{}])[0].get('status', 'Unknown')}")
    else:
        print(f"Error: {data}")

# Example Usage
message_id = "wamid.HBgMMjU0NzM3OTUzMTI0FQIAERgSMjk0NTlCMDgxMEZCNDYyQTlBAA=="  # Replace with your message ID
check_whatsapp_status(message_id)
