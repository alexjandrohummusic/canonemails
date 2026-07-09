"""Verificador de DNS in-app (SPF/DKIM/DMARC/MX) usando DNS-over-HTTPS."""
import httpx
from fastapi import APIRouter, Depends
from ..deps import current_user
from .. import models

router = APIRouter(prefix="/api/domain", tags=["domain"])

def _q(name: str, rtype: str):
    try:
        r = httpx.get("https://dns.google/resolve", params={"name": name, "type": rtype}, timeout=8)
        ans = r.json().get("Answer", [])
        return [a.get("data", "") for a in ans]
    except Exception:
        return []

@router.get("/check")
def check(domain: str, u: models.User = Depends(current_user)):
    sub = f"send.{domain}"
    spf = [d for d in _q(sub, "TXT") if "spf1" in d.lower()]
    mx = _q(sub, "MX")
    dkim = _q(f"resend._domainkey.{domain}", "TXT")
    dmarc = [d for d in _q(f"_dmarc.{domain}", "TXT") if "dmarc1" in d.lower()]
    ok = bool(spf and mx and dkim)
    return {"domain": domain, "spf": bool(spf), "mx": bool(mx), "dkim": bool(dkim),
            "dmarc": bool(dmarc), "verified": ok}
