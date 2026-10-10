import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

class Settings:
    PGHOST = os.getenv("PGHOST", "192.168.171.158")
    PGPORT = int(os.getenv("PGPORT", "5432"))
    PGDATABASE = os.getenv("PGDATABASE", "postgres")
    PGUSER = os.getenv("PGUSER", "postgres")
    PGPASSWORD = os.getenv("PGPASSWORD", "Mudar@123")
    PGSCHEMA = os.getenv("PGSCHEMA", "pluraal")
    
    JWT_SECRET = os.getenv("JWT_SECRET", "pluraal-super-secret-key-2026-secure-jwt-token")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 12

    MIN_PASSWORD_LENGTH = 8
    TEMP_PASSWORD_LENGTH = 10

settings = Settings()
