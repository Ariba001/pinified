def send_email(to_email, subject, body):
    print(f"[SIMULATED EMAIL] → {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    return "simulated_email_id"


# import smtplib
# from email.mime.text import MIMEText
# import os
# from dotenv import load_dotenv

# load_dotenv()

# EMAIL = os.getenv("EMAIL_USER")
# PASSWORD = os.getenv("EMAIL_PASS")


# def send_email(to_email, subject, body):
#     '''
#     Sends email using SMTP (Gmail)
#     '''

#     try:
#         msg = MIMEText(body)
#         msg["Subject"] = subject
#         msg["From"] = EMAIL
#         msg["To"] = to_email

#         with smtplib.SMTP("smtp.gmail.com", 587) as server:
#             server.starttls()
#             server.login(EMAIL, PASSWORD)
#             server.send_message(msg)

#         return True

#     except Exception as e:
#         print("Email Error:", e)
#         return False
# """