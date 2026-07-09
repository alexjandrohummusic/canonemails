"""Envío vía Resend con el token del usuario (BYO)."""
import httpx

def send_email(resend_token: str, from_name: str, from_email: str, to: str,
               subject: str, html: str, text: str) -> str:
    if not resend_token:
        raise ValueError("Falta el token de Resend (BYO).")
    frm = f"{from_name} <{from_email}>" if from_name else from_email
    r = httpx.post("https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {resend_token}", "Content-Type": "application/json"},
        json={"from": frm, "to": [to], "subject": subject, "html": html, "text": text},
        timeout=30)
    r.raise_for_status()
    return r.json().get("id", "")
