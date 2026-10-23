#!/usr/bin/env python3
"""Email a payment reminder to clients with overdue invoices."""
import csv
import os
import smtplib
import sys
from email.message import EmailMessage

LEDGER = "/home/accounts/shared/ledger/overdue.csv"


def build(row):
    msg = EmailMessage()
    msg["From"] = os.environ["SMTP_FROM"]
    msg["To"] = row["client_email"]
    msg["Subject"] = f"Reminder: invoice {row['invoice_no']} is overdue"
    msg.set_content(
        f"Dear {row['client_name']},\n\n"
        f"Our records show invoice {row['invoice_no']} for {row['amount']} "
        f"was due on {row['due_date']}.\n\n"
        f"{row['notes']}\n\n"
        "Please arrange payment at your earliest convenience.\n"
    )
    return msg


def main():
    if "--all" not in sys.argv:
        print("usage: send_reminders.py --all")
        return 1
    with open(LEDGER, newline="") as f:
        rows = list(csv.DictReader(f))
    server = smtplib.SMTP(os.environ["SMTP_HOST"], 587)
    server.starttls()
    server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    sent = 0
    for row in rows:
        server.send_message(build(row))
        sent += 1
    server.quit()
    print(f"sent {sent} reminders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
