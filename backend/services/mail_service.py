import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.core.config import SMTP_SERVER, SMTP_PORT, EMAIL, PASSWORD
from backend.core.logger import get_logger
from backend.utils.exceptions import SMTPError

logger = get_logger("mail_service")


def send_mail(to_email: str, subject: str, body: str) -> bool:
    logger.info(f"Sending mail | to={to_email} subject={subject}")

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"Mail sent | to={to_email}")
        _audit_email(to_email, subject, "SUCCESS")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        _audit_email(to_email, subject, "FAILURE", "SMTP auth failed")
        raise SMTPError(
            "SMTP Authentication Failed. Use a Gmail App Password instead of your account password."
        )

    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection error: {e}")
        _audit_email(to_email, subject, "FAILURE", "SMTP connection error")
        raise SMTPError("Unable to connect to SMTP server.")

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        _audit_email(to_email, subject, "FAILURE", str(e))
        raise SMTPError(str(e))

    except Exception as e:
        logger.error(f"Unexpected mail error ({type(e).__name__}): {e}")
        _audit_email(to_email, subject, "FAILURE", str(e))
        raise


def _audit_email(to_email: str, subject: str, status: str, detail: str | None = None):
    try:
        from backend.repositories.audit_repository import log_action
        log_action("EMAIL_SENT", status=status, entity="EMAIL",
                   entity_id=to_email, detail=detail or subject)
    except Exception:
        pass  # audit failure must never mask the original mail error
