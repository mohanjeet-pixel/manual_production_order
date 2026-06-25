import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

APP_URL = os.getenv("APP_URL")