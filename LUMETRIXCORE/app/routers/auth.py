import os, traceback
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models
from ..security import hash_password, verify_password, make_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

class Cred(BaseModel):
    email: EmailStr
    password: str
    name: str = ""

def _seed_config(db: Session, user_id: int):
    for kind, fn in [("catalogo", "catalogo.PLANTILLA.json"), ("afinidad", "afinidad.txt"), ("config", "config.txt")]:
        content = ""
        try:
            path = os.path.join(DATA, fn)
            if os.path.exists(path):
                content = open(path, encoding="utf-8").read()
        except Exception:
            content = ""
        db.add(models.ConfigFile(user_id=user_id, kind=kind, content=content))
    db.commit()

@router.post("/register")
def register(c: Cred, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(email=str(c.email)).first():
        raise HTTPException(400, "Ese correo ya está registrado.")
    try:
        u = models.User(email=str(c.email), name=c.name, password_hash=hash_password(c.password),
                        from_name=c.name or "Mi marca")
        db.add(u); db.commit(); db.refresh(u)
        _seed_config(db, u.id)
        return {"token": make_token(u.id), "user": {"id": u.id, "email": u.email, "name": u.name}}
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"No se pudo registrar: {type(e).__name__}: {e}")

@router.post("/login")
def login(c: Cred, db: Session = Depends(get_db)):
    u = db.query(models.User).filter_by(email=str(c.email)).first()
    if not u or not verify_password(c.password, u.password_hash):
        raise HTTPException(401, "Credenciales inválidas.")
    return {"token": make_token(u.id), "user": {"id": u.id, "email": u.email, "name": u.name}}
