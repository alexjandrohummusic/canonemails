"""Render dinámico: auto-detecta el tipo de bloque y lo renderiza en el tema elegido.
Devuelve (asunto, html, texto_plano)."""
from jinja2 import Template
from .themes import get as get_theme

_SHELL = Template("""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{{t.bg}};margin:0;padding:0;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:{{t.card}};border-radius:{{t.radius}};overflow:hidden;font-family:{{t.font}};color:{{t.ink}};">
<tr><td style="height:6px;background:{{t.accent}};"></td></tr>
<tr><td style="padding:26px 30px 6px 30px;">
<p style="margin:0 0 14px 0;font-size:15px;color:{{t.ink}};">Hola {{nombre}},</p>
{{ content }}
</td></tr>
<tr><td style="padding:18px 30px 26px 30px;border-top:1px solid rgba(120,120,120,0.18);">
<p style="margin:0;font-size:11px;color:#8a97a8;">Recibes este correo porque eres cliente de {{from_name}}.
<a href="{{unsub}}" style="color:#8a97a8;">Darse de baja</a>.</p>
</td></tr>
</table></td></tr></table>
""")

_TSL = Template("""
{% for para in paras %}<p style="margin:0 0 12px 0;font-size:15px;line-height:1.55;color:{{t.ink}};">{{para}}</p>
{% endfor %}
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:14px 0 6px 0;"><tr>
<td align="center" style="background:{{t.accent}};border-radius:{{t.radius}};">
<a href="{{url}}" style="display:inline-block;padding:12px 26px;font-family:{{t.font}};font-size:15px;font-weight:bold;color:#ffffff;text-decoration:none;">Conocer más &rarr;</a>
</td></tr></table>
""")

_CROSS = Template("""
<p style="margin:0 0 14px 0;font-size:15px;line-height:1.5;color:{{t.ink}};">Elegí estas recomendaciones pensando en ti:</p>
{% for it in items %}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 12px 0;border:1px solid rgba(120,120,120,0.2);border-radius:{{t.radius}};">
<tr><td style="padding:14px 16px;">
<p style="margin:0 0 5px 0;font-size:15px;font-weight:bold;color:{{t.brand}};">{{it.nombre}}</p>
<p style="margin:0 0 10px 0;font-size:13px;line-height:1.45;color:{{t.ink}};">{{it.descripcion}}</p>
<a href="{{it.link}}" style="display:inline-block;padding:8px 18px;background:{{t.accent}};border-radius:{{t.radius}};font-size:13px;font-weight:bold;color:#ffffff;text-decoration:none;">Ver más &rarr;</a>
</td></tr></table>
{% endfor %}
""")

def _subject(block):
    return (block.get("asunto") or "").replace("{{nombre}}", block.get("nombre", "")).strip()

def render(block: dict, from_name: str, theme_name: str, unsub_url: str = "#"):
    t = get_theme(theme_name)
    if block["type"] == "tsl":
        paras = [p for p in block.get("cuerpo", "").split("\n\n") if p.strip()]
        content = _TSL.render(t=t, paras=paras, url=block.get("url", "#"))
        text = block.get("cuerpo", "") + "\n\n" + block.get("url", "")
    else:
        content = _CROSS.render(t=t, items=block.get("items", []))
        text = "\n".join(f"- {i['nombre']}: {i['link']}" for i in block.get("items", []))
    html = _SHELL.render(t=t, nombre=block.get("nombre", ""), content=content,
                         from_name=from_name, unsub=unsub_url)
    return _subject(block), html, text
