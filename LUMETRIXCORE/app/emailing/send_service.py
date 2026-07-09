"""Servicio de envío con pacing anti-spam. Auto-detecta el formato de cada bloque
y respeta supresión, idempotencia (no reenvía 'sent') y umbrales. Un solo archivo
consolidado por campaña -> una sola cola de envío."""
import json, time, random, datetime
from ..config import settings
from ..db import SessionLocal
from .. import models
from ..security import decrypt
from .render import render
from .sender import send_email

def send_campaign(campaign_id: int):
    db = SessionLocal()
    try:
        camp = db.get(models.Campaign, campaign_id)
        if not camp:
            return
        user = db.get(models.User, camp.user_id)
        if user.subscription_status != "active":
            camp.status = "error"; db.commit(); return
        resend_token = decrypt(user.resend_token_enc)
        blocks = json.loads(camp.blocks_json)
        supp = {s.email.lower() for s in db.query(models.Suppression).filter_by(user_id=user.id)}
        # asegurar filas de destinatarios (idempotencia)
        existing = {r.email.lower(): r for r in db.query(models.Recipient).filter_by(campaign_id=camp.id)}
        for b in blocks:
            if b["email"].lower() not in existing:
                r = models.Recipient(campaign_id=camp.id, email=b["email"], state="queued")
                db.add(r); existing[b["email"].lower()] = r
        db.commit()
        camp.status = "sending"; db.commit()

        sent_this_hour = 0; sent_today = 0; count = 0
        for b in blocks:
            rec = existing[b["email"].lower()]
            if rec.state == "sent":       # idempotente
                continue
            if b["email"].lower() in supp:
                rec.state = "skipped"; db.commit(); continue
            # topes de warm-up (config)
            if sent_this_hour >= settings.WARMUP_MAX_PER_HOUR or sent_today >= settings.WARMUP_MAX_PER_DAY:
                camp.status = "paused"; db.commit(); break
            try:
                subject, html, text = render(b, user.from_name, user.template,
                    unsub_url=f"mailto:{user.from_email}?subject=Baja")
                pid = send_email(resend_token, user.from_name, user.from_email,
                                 b["email"], subject, html, text)
                rec.state = "sent"; rec.provider_id = pid
                camp.sent += 1; sent_this_hour += 1; sent_today += 1
            except Exception:
                rec.state = "failed"; camp.failed += 1
            db.commit()
            count += 1
            # pacing: pausa cada N y jitter entre correos
            if count % settings.SEND_PAUSE_EVERY == 0:
                time.sleep(settings.SEND_PAUSE_SECONDS)
                sent_this_hour = 0
            else:
                time.sleep(random.uniform(settings.SEND_MIN_DELAY_SEC, settings.SEND_MAX_DELAY_SEC))
        if camp.status == "sending":
            camp.status = "done"
        db.commit()
    finally:
        db.close()
