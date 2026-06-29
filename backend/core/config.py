import os
from dotenv import load_dotenv

load_dotenv()

# SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Application
APP_URL = os.getenv("APP_URL", "http://192.168.23.44:8000")

# Database — single source of truth
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "Manual_order"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "bull@123"),
}

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours

# SAP API
SAP_API_URL      = os.getenv("SAP_API_URL", "http://172.16.1.68:8000/sap/bc/zorderapi?sap-client=900 ")
SAP_USERNAME     = os.getenv("SAP_USERNAME", "bulladm")
SAP_PASSWORD     = os.getenv("SAP_PASSWORD", "ce@123")
