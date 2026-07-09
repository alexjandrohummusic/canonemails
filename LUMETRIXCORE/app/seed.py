import os
from .db import SessionLocal
from . import models
from .security import hash_password
from .config import settings

def seed_admin():
    db = SessionLocal()
    try:
        if db.query(models.User).filter_by(email=settings.ADMIN_EMAIL).first():
            return
        u = models.User(email=settings.ADMIN_EMAIL, name="Admin",
                        password_hash=hash_password(settings.ADMIN_PASSWORD), from_name="Mi marca")
        db.add(u); db.commit(); db.refresh(u)
        db.commit()
    finally:
        db.close()
