"""Almacenamiento por cliente: una carpeta por correo con sus archivos."""
import os, re
BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tenants")

def slug(email: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (email or "").lower()).strip("_") or "tenant"

def tdir(email: str) -> str:
    d = os.path.join(BASE, slug(email))
    os.makedirs(os.path.join(d, "entradas", "ventas"), exist_ok=True)
    os.makedirs(os.path.join(d, "salidas"), exist_ok=True)
    return d

def path(email, *parts): return os.path.join(tdir(email), *parts)
def exists(email, *parts): return os.path.exists(os.path.join(tdir(email), *parts))
def read(email, *parts):
    p = os.path.join(tdir(email), *parts)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
def write(email, content, *parts):
    p = os.path.join(tdir(email), *parts); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(content); return p
def write_bytes(email, content, *parts):
    p = os.path.join(tdir(email), *parts); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(content); return p

def save_sales(email, content: bytes, filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower() or ".csv"
    # limpiar ventas anteriores
    vd = os.path.join(tdir(email), "entradas", "ventas")
    for f in os.listdir(vd):
        try: os.remove(os.path.join(vd, f))
        except Exception: pass
    return write_bytes(email, content, "entradas", "ventas", "actual" + ext)

def current_sales(email):
    vd = os.path.join(tdir(email), "entradas", "ventas")
    files = [f for f in os.listdir(vd)] if os.path.isdir(vd) else []
    if not files: return None, None
    fn = files[0]
    return open(os.path.join(vd, fn), "rb").read(), fn
