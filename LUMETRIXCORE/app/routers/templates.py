from fastapi import APIRouter, Depends
from ..deps import current_user
from ..emailing.themes import THEMES
from ..emailing.render import render
from .. import models

router = APIRouter(prefix="/api/templates", tags=["templates"])

_SAMPLE_TSL = {"type": "tsl", "nombre": "Ana", "asunto": "Lo que no sabías", "producto": "Producto demo",
               "cuerpo": "Este es un ejemplo de carta de ventas.\n\nMuestra cómo se ve el diseño con un párrafo y un botón.",
               "url": "https://ejemplo.com"}
_SAMPLE_CROSS = {"type": "crosssell", "nombre": "Ana", "asunto": "Para ti",
                 "items": [{"nombre": "Producto A", "descripcion": "Descripción breve del producto A.", "link": "#"},
                           {"nombre": "Producto B", "descripcion": "Descripción breve del producto B.", "link": "#"}]}

@router.get("")
def list_templates(u: models.User = Depends(current_user)):
    return [{"id": k, "nombre": v["nombre"], "actual": (k == u.template)} for k, v in THEMES.items()]

@router.get("/{theme}/preview")
def preview_theme(theme: str, kind: str = "tsl", u: models.User = Depends(current_user)):
    block = _SAMPLE_TSL if kind == "tsl" else _SAMPLE_CROSS
    _, html, _ = render(block, u.from_name or "Mi marca", theme)
    return {"theme": theme, "html": html}
