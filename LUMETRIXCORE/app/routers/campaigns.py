import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import current_user
from .. import models
from ..config import settings
from ..security import decrypt
from .. import storage
from ..core.campaign import generate
from ..emailing.render import render

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

def _cfg(db, uid, kind):
    cf = db.query(models.ConfigFile).filter_by(user_id=uid, kind=kind).first()
    return cf.content if cf else ""

@router.post("/generate")
async def generate_campaign(background: BackgroundTasks, mode: str = Form("auto"),
        u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    sales, sname = storage.current_sales(u.email)
    if not sales:
        raise HTTPException(400, "Primero sube tu lista de ventas (pestaña Datos).")
    if not storage.exists(u.email, "entradas", "catalogo.json"):
        raise HTTPException(400, "Primero completa tu catálogo (pestaña Datos).")
    token = settings.PLATFORM_AI_TOKEN if settings.AI_MODE == "managed" else decrypt(u.claude_token_enc)
    supp = {sp.email.lower() for sp in db.query(models.Suppression).filter_by(user_id=u.id)}
    res = generate(sales, sname,
                   storage.read(u.email, "entradas", "catalogo.json"),
                   storage.read(u.email, "entradas", "afinidad.txt"),
                   storage.read(u.email, "entradas", "config.txt"),
                   supp, token, forced_mode=mode)
    if res.get("error"):
        raise HTTPException(422, res)
    camp = models.Campaign(user_id=u.id, mode=mode, blocks_json=json.dumps(res["blocks"], ensure_ascii=False),
                           report_json=json.dumps(res["report"], ensure_ascii=False), total=len(res["blocks"]))
    db.add(camp); db.commit(); db.refresh(camp)
    # respaldo del blast en la carpeta del cliente (oculto para él)
    storage.write(u.email, json.dumps(res["blocks"], ensure_ascii=False, indent=1), "salidas", f"campana_{camp.id}.json")
    return {"campaign_id": camp.id, "report": res["report"]}

@router.get("/{cid}/preview")
def preview(cid: int, u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    camp = db.get(models.Campaign, cid)
    if not camp or camp.user_id != u.id:
        raise HTTPException(404, "Campaña no encontrada")
    blocks = json.loads(camp.blocks_json)[:3]   # solo los primeros 3
    out = []
    for b in blocks:
        subj, html, _ = render(b, u.from_name, u.template)
        out.append({"type": b["type"], "email": b["email"], "asunto": subj, "html": html})
    return {"previews": out, "template": u.template}

@router.post("/{cid}/send")
def send(cid: int, background: BackgroundTasks, u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    camp = db.get(models.Campaign, cid)
    if not camp or camp.user_id != u.id:
        raise HTTPException(404, "Campaña no encontrada")
    if not u.resend_token_enc:
        raise HTTPException(400, "Falta el token de Resend (Ajustes → Envío).")
    if u.subscription_status != "active":
        raise HTTPException(402, "Suscripción no activa.")
    if settings.SEND_MODE == "celery":
        from ..workers.celery_app import send_campaign_task
        send_campaign_task.delay(camp.id)
    else:
        from ..emailing.send_service import send_campaign
        background.add_task(send_campaign, camp.id)
    camp.status = "sending"; db.commit()
    return {"ok": True, "status": "sending"}

@router.get("/{cid}")
def status(cid: int, u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    camp = db.get(models.Campaign, cid)
    if not camp or camp.user_id != u.id:
        raise HTTPException(404, "Campaña no encontrada")
    return {"id": camp.id, "status": camp.status, "mode": camp.mode, "total": camp.total,
            "sent": camp.sent, "failed": camp.failed, "report": json.loads(camp.report_json)}

@router.get("")
def list_campaigns(u: models.User = Depends(current_user), db: Session = Depends(get_db)):
    cs = db.query(models.Campaign).filter_by(user_id=u.id).order_by(models.Campaign.id.desc()).all()
    return [{"id": c.id, "status": c.status, "mode": c.mode, "total": c.total, "sent": c.sent} for c in cs]
