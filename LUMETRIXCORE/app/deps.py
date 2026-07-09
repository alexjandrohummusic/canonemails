from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .db import get_db
from .security import read_token
from . import models

def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> models.User:
    token = authorization.replace("Bearer ", "").strip()
    uid = read_token(token)
    if not uid:
        raise HTTPException(401, "No autorizado")
    u = db.get(models.User, uid)
    if not u:
        raise HTTPException(401, "Usuario no encontrado")
    return u
