"""Carga y validación de configuración del usuario: catálogo, afinidad, config."""
import json, re

def load_config(text: str) -> dict:
    cfg = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()
    def f(k, d):
        try: return float(cfg.get(k, d))
        except Exception: return d
    def i(k, d):
        try: return int(float(cfg.get(k, d)))
        except Exception: return d
    return {
        "PESO_ULTIMO_PRODUCTO": f("PESO_ULTIMO_PRODUCTO", 0.7),
        "PESO_RESTO_HISTORIAL": f("PESO_RESTO_HISTORIAL", 0.3),
        "PESO_AFINIDAD_FAMILIAR": f("PESO_AFINIDAD_FAMILIAR", 0.4),
        "PESO_AFINIDAD_ESPECIFICA": f("PESO_AFINIDAD_ESPECIFICA", 0.6),
        "PISO_AFINIDAD": f("PISO_AFINIDAD", 15),
        "AFINIDAD_WELLNESS_CRUZADO": f("AFINIDAD_WELLNESS_CRUZADO", 30),
        "AFINIDAD_MISMA_FAMILIA_DEFAULT": f("AFINIDAD_MISMA_FAMILIA_DEFAULT", 50),
        "ESTATUS_VALIDOS": [s.strip() for s in cfg.get("ESTATUS_VALIDOS", "Aprobado,Completo").split(",")],
        "CANDIDATOS_INICIALES": i("CANDIDATOS_INICIALES", 8),
        "PRODUCTOS_OUTPUT": i("PRODUCTOS_OUTPUT", 4),
        "UMBRAL_CANIBALIZACION": f("UMBRAL_CANIBALIZACION", 85),
        "UMBRAL_DIRECTO": f("UMBRAL_DIRECTO", 75),
        "UMBRAL_RELACIONADO": f("UMBRAL_RELACIONADO", 50),
        "UMBRAL_EXPLORATORIO": f("UMBRAL_EXPLORATORIO", 30),
        "TSL_ANCLA_MIN_SIMILARIDAD": f("TSL_ANCLA_MIN_SIMILARIDAD", 40),
        "TSL_TOLERANCIA_LONGITUD": f("TSL_TOLERANCIA_LONGITUD", 0.10),
        "TSL_LONGITUD_OBJETIVO": i("TSL_LONGITUD_OBJETIVO", 900),
        "ASUNTOS_POR_INTERES": i("ASUNTOS_POR_INTERES", 5),
        "ASUNTO_MAX_CARACTERES": i("ASUNTO_MAX_CARACTERES", 50),
        "_raw": cfg,
    }

def load_afinidad(text: str) -> dict:
    fam, sub, well, vec = [], {}, set(), {}
    sec = None
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("["):
            sec = s.strip("[]").upper(); continue
        if sec == "FAMILIAS":
            fam.append(s)
        elif sec == "SUBCATEGORIAS":
            if ":" in s:
                fm, subs = s.split(":", 1)
                sub[fm.strip()] = [x.strip() for x in subs.split(",") if x.strip()]
        elif sec == "WELLNESS":
            for x in s.split(","):
                well.add(x.strip())
        elif sec == "VECINDADES":
            if "<->" in s and ":" in s:
                left, val = s.rsplit(":", 1)
                a, b = left.split("<->", 1)
                try:
                    v = int(val.strip()); vec[(a.strip(), b.strip())] = v; vec[(b.strip(), a.strip())] = v
                except ValueError:
                    pass
    return {"familias": fam, "subcategorias": sub, "wellness": well, "vecindades": vec}

def load_catalogo(text: str):
    data = json.loads(text)
    cat = data["catalogo"] if isinstance(data, dict) and "catalogo" in data else data
    principales = [p for p in cat if p.get("esPrincipal") and str(p.get("linkLanding", "")).strip()]
    by_name = {str(p["nombre"]).strip(): p for p in cat}
    return cat, principales, by_name

def categorias_definidas(af: dict) -> set:
    d = set()
    for fam, subs in af["subcategorias"].items():
        for su in subs:
            d.add(f"{fam}/{su}")
    return d

def validar_categorias(cat, af):
    """Devuelve lista de (categoria, nombre, id) no definidas en afinidad (PASO 4)."""
    definidas = categorias_definidas(af)
    return [(p["categoria"], p["nombre"], p.get("id")) for p in cat if p.get("categoria") not in definidas]
