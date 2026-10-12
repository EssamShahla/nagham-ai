import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def send_verification_email(to_email: str, otp: str):
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        raise RuntimeError("Email configuration is missing")

    message = EmailMessage()
    message["Subject"] = "Nagham AI - Email Verification"
    message["From"] = f"Nagham AI <{EMAIL_ADDRESS}>"
    message["To"] = to_email

    message.set_content(
        f"""
Welcome to Nagham AI!

Your verification code is:

{otp}

This code expires in 5 minutes.

If you did not create this account, you can ignore this email.

Nagham AI
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        smtp.send_message(message)


def send_password_reset_email(to_email: str, otp: str):
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        raise RuntimeError("Email configuration is missing")

    message = EmailMessage()
    message["Subject"] = "Nagham AI - Password Reset Code"
    message["From"] = f"Nagham AI <{EMAIL_ADDRESS}>"
    message["To"] = to_email

    message.set_content(
        f"""
We received a request to reset the password for your Nagham AI account.

Your password reset code is:

{otp}

This code expires in 15 minutes.

If you did not request this, you can safely ignore this email -- your
password will not be changed.

Nagham AI
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        smtp.send_message(message)