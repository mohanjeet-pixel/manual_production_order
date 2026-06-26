import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.core.config import (
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL,
    PASSWORD
)


def send_mail(to_email, subject, body):

    print("\n========== EMAIL DEBUG ==========")
    print("SMTP Server :", SMTP_SERVER)
    print("SMTP Port   :", SMTP_PORT)
    print("From        :", EMAIL)
    print("To          :", to_email)

    try:

        msg = MIMEMultipart()

        msg["From"] = EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        print("Connecting to SMTP Server...")

        server = smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30
        )

        server.set_debuglevel(1)

        print("Connected Successfully")

        server.ehlo()

        print("Starting TLS...")

        server.starttls()

        server.ehlo()

        print("Logging into Gmail...")

        server.login(
            EMAIL,
            PASSWORD
        )

        print("SMTP Login Successful")

        server.send_message(msg)

        print("MAIL SENT SUCCESSFULLY")

        server.quit()

        return True

    except smtplib.SMTPAuthenticationError as e:

        print("\nSMTP Authentication Failed")
        print(e)

        raise Exception(
            "SMTP Authentication Failed.\n"
            "Use a Gmail App Password instead of your Gmail password."
        )

    except smtplib.SMTPConnectError as e:

        print("\nSMTP Connection Error")
        print(e)

        raise Exception(
            "Unable to connect to Gmail SMTP Server."
        )

    except smtplib.SMTPException as e:

        print("\nSMTP Error")
        print(e)

        raise Exception(str(e))

    except Exception as e:

        print("\nGeneral Mail Error")
        print(type(e).__name__)
        print(e)

        raise
