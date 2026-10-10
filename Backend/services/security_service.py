import bcrypt
import jwt
import secrets
import string
from datetime import datetime, timezone, timedelta
from Backend.config.settings import settings

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def generate_temporary_password(length: int = 10) -> str:
    """Generate secure temporary password with upper, lower, digits and symbols."""
    if length < 8:
        length = 8
    
    uppers = string.ascii_uppercase
    lowers = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%&*"
    
    # Guarantee at least one of each category
    password = [
        secrets.choice(uppers),
        secrets.choice(lowers),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]
    
    all_chars = uppers + lowers + digits + symbols
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle for randomness
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expirado. Por favor, realize o login novamente.")
    except jwt.InvalidTokenError:
        raise ValueError("Token inválido.")
