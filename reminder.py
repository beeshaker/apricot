import schedule
import time
import logging
import os
from dotenv import load_dotenv
from conn import MySQLDatabase
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Starting Lease Reminder Script...")

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
GMAIL_P = os.getenv("GMAIL_P")

# Validate environment variables
if not ACCESS_TOKEN or not PHONE_NUMBER_ID or not VERSION:
    logging.error("Missing required environment variables. Please check your .env file.")
    exit(1)

# WhatsApp API URL
WHATSAPP_API_URL = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

# Initialize database connection
try:
    db = MySQLDatabase()
    logging.info("Database connection established successfully.")
except Exception as e:
    logging.error(f"Database connection failed: {e}")
    exit(1)

# Function to send WhatsApp message
def send_whatsapp(to_phone, tenant_name, expiry_date):
    logging.info(f"Sending WhatsApp message to {to_phone}...")

    # Convert expiry_date from datetime to string
    expiry_date_str = expiry_date.strftime("%Y-%m-%d")  # Format: YYYY-MM-DD

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    message_data = {
        "messaging_product": "whatsapp",
        "to": to_phone,  # Full international format (e.g., "254712345678")
        "type": "template",
        "template": {
            "name": "account_creation_confirmation_3",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": tenant_name},
                        {"type": "text", "text": expiry_date_str}  # Convert date to string
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(message_data))
        response_data = response.json()

        if response.status_code == 200:
            logging.info(f"WhatsApp message successfully sent to {to_phone}. Response: {response_data}")
        else:
            logging.error(f"Failed to send WhatsApp message. Status Code: {response.status_code}, Response: {response_data}")
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")

# Function to send email
def send_email(to_email, tenant_name, expiry_date):
    sender_email = "tekne6008@gmail.com"
    sender_password = GMAIL_P

    logging.info(f"Sending email to {to_email}...")

    subject = "Lease Expiry Reminder"
    body = f"""
    Dear {tenant_name},

    This is a reminder that your lease is set to expire on {expiry_date}. 
    Please make the necessary arrangements.

    Regards,
    Lease Management Team
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        logging.info(f"Email successfully sent to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}. Error: {e}")

# Function to check and send reminders
def check_and_notify():
    logging.info("Fetching leases for reminders...")

    try:
        leases = db.fetch_leases_for_reminder()
        logging.debug(f"Fetched leases: {leases}")

        if not leases:
            logging.info("No leases found that require reminders.")
            return

        for lease in leases:
            lease_id,  expiry_date = lease
            logging.info(f"Processing lease {lease_id}  (Expiring: {expiry_date})")

            #send_email("abhishekshah546@gmail.com", "test", expiry_date)
            send_whatsapp("+254 737 953124","test", expiry_date)

    except Exception as e:
        logging.error(f"Error fetching leases: {e}")

# Schedule the script to run daily at 9:23 AM
logging.info("Scheduling task to run at 09:40 AM daily.")
#schedule.every().day.at("10:56").do(check_and_notify)
check_and_notify()

# Run the scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(86400)  # Check every second for pending tasks
