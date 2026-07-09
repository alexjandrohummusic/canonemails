import datetime
from passlib.context import CryptContext
from jose import jwt
from .config import settings

pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# --- Vault DESACTIVADO (MVP): los tokens BYO se guardan sin cifrar por ahora ---
def encrypt(text: str) -> str:
    return text or ""

def decrypt(token: str) -> str:
    return token or ""

def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)

def make_token(user_id: int) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.APP_SECRET, algorithm="HS256")

def read_token(token: str) -> int | None:
    try:
        data = jwt.decode(token, settings.APP_SECRET, algorithms=["HS256"])
        return int(data["sub"])
    except Exception:
        return None
