# Lease Management System - Setup Guide

## Overview
This system includes:
1. A **Streamlit Dashboard** for lease management.
2. A **Lease Reminder Service** that runs continuously to send daily email reminders for expiring leases.

## Prerequisites
Ensure you have the following installed:
- Python 3.x
- Streamlit
- MySQL (for database connection)
- SMTP email credentials

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/lease-management.git
   cd lease-management
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure the email credentials in `lease_reminder.py`:
   ```python
   EMAIL_SENDER = "your_email@example.com"
   EMAIL_PASSWORD = "your_email_password"
   ```
4. Ensure your MySQL database is configured correctly in `conn.py`.

## Running the Application
### 1️⃣ Start the Streamlit Dashboard
Run the following command in a terminal:
```sh
streamlit run app.py
```

### 2️⃣ Start the Lease Reminder Service
Run this in a separate terminal:
```sh
nohup python lease_reminder.py &
```
This ensures the reminder service runs in the background continuously.

## Checking Logs
Logs are stored in `lease_reminder.log`.

### View logs in real-time:
```sh
tail -f lease_reminder.log
```

### Check all emails sent:
```sh
cat lease_reminder.log | grep "Email sent"
```

### Check for errors:
```sh
cat lease_reminder.log | grep "Error"
```

## Stopping the Reminder Service
To stop the running reminder service, use:
```sh
pkill -f lease_reminder.py
```

## Troubleshooting
1. If emails are not being sent, check the SMTP credentials.
2. If no reminders are being sent, verify the database lease data.
3. Check logs for detailed error messages.

## Future Enhancements
- Add WhatsApp reminders using Twilio
- Integrate a task queue for better scheduling

🚀 **Happy Leasing!**

Hello {{1}}, this is a reminder that your lease expires on {{2}}. Please take the necessary actions.
