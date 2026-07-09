"""Cliente de IA con token del usuario (BYO Claude). Degradación elegante:
si no hay token o falla, devuelve None y el motor usa el respaldo determinista."""
import json
from ..config import settings

def available(token: str) -> bool:
    return bool(token and token.strip())

def _client(token: str):
    from anthropic import Anthropic
    return Anthropic(api_key=token)

# Alias legibles -> string exacto del modelo (Anthropic API)
MODEL_ALIASES = {
    "haiku":  "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
    "opus":   "claude-opus-4-8",
    "fable":  "claude-fable-5",
}
def model_id() -> str:
    m = (settings.AI_MODEL or "haiku").strip()
    return MODEL_ALIASES.get(m.lower(), m)  # si no es alias, se usa tal cual

def write_tsl(token: str, ficha: dict, ancla: str | None, objetivo: int) -> str | None:
    if not available(token):
        return None
    prompt = (
        "Escribe el CUERPO de una carta de ventas (TSL) en español, 2a persona, frases cortas, "
        f"~{objetivo} caracteres (±10%). NO inicies con saludo. Sin links, sin cupones, sin promesas médicas. "
        "Estructura: gancho, agitación, puente al producto, promesa+mecanismo, prueba, urgencia honesta, cierre que invita a leer.\n"
        f"Producto: {ficha.get('nombre')}\nPromesa/idea: {ficha.get('curiosity','')}\nDescripción: {ficha.get('corta','')}\n"
        + (f"Conecta con lo que ya compró: {ancla}\n" if ancla else "Abre con la tensión del problema (sin ancla).\n")
        + "Devuelve SOLO el cuerpo."
    )
    try:
        r = _client(token).messages.create(model=model_id(), max_tokens=600,
            messages=[{"role": "user", "content": prompt}])
        return r.content[0].text.strip()
    except Exception:
        return None

def write_subjects(token: str, ficha: dict, n: int, maxlen: int) -> list | None:
    if not available(token):
        return None
    prompt = (
        f"Genera {n} asuntos de correo distintos en español para este producto, curiosity gap, "
        f"máx {maxlen} caracteres, sin '|', sin MAYÚSCULAS sostenidas, sin 'GRATIS', sin '$', sin signos múltiples. "
        "Pueden usar {{nombre}}. Devuelve un JSON array de strings.\n"
        f"Producto: {ficha.get('nombre')}\nIdea: {ficha.get('curiosity','')}"
    )
    try:
        r = _client(token).messages.create(model=model_id(), max_tokens=300,
            messages=[{"role": "user", "content": prompt}])
        txt = r.content[0].text.strip()
        arr = json.loads(txt[txt.find("["): txt.rfind("]") + 1])
        return [str(a)[:maxlen] for a in arr][:n]
    except Exception:
        return None
