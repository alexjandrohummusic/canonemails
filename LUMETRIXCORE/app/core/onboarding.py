"""Genera automáticamente los archivos de configuración que el cliente NO toca:
- catálogo (plantilla con los productos del archivo de ventas, para llenar a mano),
- afinidad (calculada de las categorías del catálogo; oculta al cliente),
- config (parámetros del motor; oculto)."""
import json

DEFAULT_CONFIG = """PESO_ULTIMO_PRODUCTO=0.7
PESO_RESTO_HISTORIAL=0.3
PESO_AFINIDAD_FAMILIAR=0.4
PESO_AFINIDAD_ESPECIFICA=0.6
PISO_AFINIDAD=15
AFINIDAD_WELLNESS_CRUZADO=30
AFINIDAD_MISMA_FAMILIA_DEFAULT=50
CANDIDATOS_INICIALES=8
PRODUCTOS_OUTPUT=4
UMBRAL_CANIBALIZACION=85
ESTATUS_VALIDOS=Aprobado,Completo
UMBRAL_DIRECTO=75
UMBRAL_RELACIONADO=50
UMBRAL_EXPLORATORIO=30
TSL_ANCLA_MIN_SIMILARIDAD=40
TSL_TOLERANCIA_LONGITUD=0.10
TSL_LONGITUD_OBJETIVO=900
ASUNTOS_POR_INTERES=5
ASUNTO_MAX_CARACTERES=50
"""

def catalog_draft(product_names) -> str:
    cat = []
    for i, n in enumerate(product_names, 1):
        cat.append({"id": i, "nombre": n, "esPrincipal": True, "linkCompra": "", "linkLanding": "",
                    "orderBumps": [], "categoria": "", "descripcionCorta": "", "descripcionCuriosity": ""})
    return json.dumps({"catalogo": cat}, ensure_ascii=False, indent=2)

def build_afinidad(catalogo_json: str) -> str:
    data = json.loads(catalogo_json)
    cat = data["catalogo"] if isinstance(data, dict) and "catalogo" in data else data
    fams = {}
    for p in cat:
        c = (p.get("categoria") or "").strip()
        if "/" not in c: continue
        fam, sub = c.split("/", 1)
        fams.setdefault(fam.strip(), set()).add(sub.strip())
    if not fams:
        return "[FAMILIAS]\n\n[SUBCATEGORIAS]\n\n[WELLNESS]\n\n[VECINDADES]\n"
    lines = ["[FAMILIAS]"] + list(fams.keys()) + ["", "[SUBCATEGORIAS]"]
    for fam, subs in fams.items():
        lines.append(f"{fam}: " + ", ".join(sorted(subs)))
    wellness = [f for f in fams if f.lower() not in ("educación", "educacion")]
    lines += ["", "[WELLNESS]", ", ".join(wellness), "", "[VECINDADES]"]
    return "\n".join(lines) + "\n"
