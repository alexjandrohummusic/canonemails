from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import current_user
from .. import models
from ..security import encrypt

router = APIRouter(prefix="/api/account", tags=["account"])

class Profile(BaseModel):
    name: str | None = None
    from_name: str | None = None
    from_email: str | None = None
    template: str | None = None

class Tokens(BaseModel):
    claude_token: str | None = None
    resend_token: str | None = None

@router.get("")
def get_me(u: models.User = Depends(current_user)):
    return {"email": u.email, "name": u.name, "from_name": u.from_name, "from_email": u.from_email,
            "template": u.template, "has_claude": bool(u.claude_token_enc), "has_resend": bool(u.resend_token_enc),
            "subscription_status": u.subscription_status}

@router.put("")
def update_me(p: Profile, u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    for k in ["name", "from_name", "from_email", "template"]:
        v = getattr(p, k)
        if v is not None:
            setattr(u, k, v)
    db.commit(); return {"ok": True}

@router.put("/tokens")
def set_tokens(t: Tokens, u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    if t.claude_token is not None:
        u.claude_token_enc = encrypt(t.claude_token)
    if t.resend_token is not None:
        u.resend_token_enc = encrypt(t.resend_token)
    db.commit(); return {"ok": True}

@router.get("/config/{kind}")
def get_config(kind: str, u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    cf = db.query(models.ConfigFile).filter_by(user_id=u.id, kind=kind).first()
    return {"kind": kind, "content": cf.content if cf else ""}

class ConfigIn(BaseModel):
    content: str

@router.put("/config/{kind}")
def put_config(kind: str, body: ConfigIn, u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    cf = db.query(models.ConfigFile).filter_by(user_id=u.id, kind=kind).first()
    if not cf:
        cf = models.ConfigFile(user_id=u.id, kind=kind); db.add(cf)
    cf.content = body.content; db.commit(); return {"ok": True}

# Webhook de Hotmart: activar/suspender cuenta según la suscripción
class HotmartEvent(BaseModel):
    email: str
    event: str           # PURCHASE_APPROVED | SUBSCRIPTION_CANCELLATION | PURCHASE_REFUNDED
    subscriber_id: str = ""

@router.post("/hotmart/webhook")
def hotmart_webhook(ev: HotmartEvent, db: Session = Depends(get_db)):
    u = db.query(models.User).filter_by(email=ev.email).first()
    if not u:
        return {"ok": True, "note": "usuario no encontrado"}
    u.hotmart_subscriber_id = ev.subscriber_id or u.hotmart_subscriber_id
    u.subscription_status = "active" if ev.event == "PURCHASE_APPROVED" else "suspended"
    db.commit(); return {"ok": True, "status": u.subscription_status}

@router.get("/validate")
def validate_config(u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    from ..core import catalog as C
    def g(kind):
        cf = db.query(models.ConfigFile).filter_by(user_id=u.id, kind=kind).first()
        return cf.content if cf else ""
    try:
        cat, principales, _ = C.load_catalogo(g("catalogo"))
    except Exception as e:
        return {"ok": False, "error": f"El catálogo no es JSON válido: {e}"}
    af = C.load_afinidad(g("afinidad"))
    nuevas = C.validar_categorias(cat, af)
    return {"ok": len(nuevas) == 0 and len(cat) > 0, "productos": len(cat), "principales": len(principales),
            "categorias_nuevas": [{"categoria": c, "producto": n} for c, n, i in nuevas]}

@router.get("/users")
def list_users(u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    # Solo el admin puede listar todos los usuarios. Quita este bloque si quieres
    # que cualquier usuario autenticado pueda hacerlo.
    from ..config import settings
    if u.email != settings.ADMIN_EMAIL:
        raise HTTPException(403, "Solo el administrador puede listar usuarios.")
    users = db.query(models.User).order_by(models.User.id).all()
    return [{"id": x.id, "email": x.email, "name": x.name, "from_name": x.from_name,
             "from_email": x.from_email, "template": x.template,
             "subscription_status": x.subscription_status, "hotmart_subscriber_id": x.hotmart_subscriber_id,
             "has_claude": bool(x.claude_token_enc), "has_resend": bool(x.resend_token_enc),
             "created_at": x.created_at} for x in users]