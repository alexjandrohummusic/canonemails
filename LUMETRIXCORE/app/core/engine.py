"""Motor de dominio: afinidad, scoring, selección de modo y salida consolidada.
Fuente de verdad única (portado del algoritmo Lumetrix)."""
from . import catalog as _cat

def split_cat(c):
    if "/" in c:
        a, b = c.split("/", 1); return a.strip(), b.strip()
    return c.strip(), ""

def calcular_afinidad(catA, catB, af, cfg):
    if catA == catB: return 100
    fa, _ = split_cat(catA); fb, _ = split_cat(catB)
    well = af["wellness"]; vec = af["vecindades"]
    if fa == fb: af_fam = 100
    elif fa in well and fb in well: af_fam = cfg["AFINIDAD_WELLNESS_CRUZADO"]
    else: af_fam = cfg["PISO_AFINIDAD"]
    if (catA, catB) in vec: af_esp = vec[(catA, catB)]
    elif fa == fb: af_esp = cfg["AFINIDAD_MISMA_FAMILIA_DEFAULT"]
    elif fa in well and fb in well: af_esp = cfg["AFINIDAD_WELLNESS_CRUZADO"]
    else: af_esp = cfg["PISO_AFINIDAD"]
    return round(af_esp * cfg["PESO_AFINIDAD_ESPECIFICA"] + af_fam * cfg["PESO_AFINIDAD_FAMILIAR"])

def cat_of(nombre, by_name):
    p = by_name.get(nombre)
    return p["categoria"] if p else None

def score(prod, cli, af, cfg, by_name, bump_bonus=False):
    if prod["nombre"] in cli["listaCompras"]:
        return 0
    cat_ult = cat_of(cli["productoPrincipal"], by_name)
    if cat_ult is None:
        return 0
    a_ult = calcular_afinidad(prod["categoria"], cat_ult, af, cfg)
    hist = [cat_of(x, by_name) for x in cli["historial"] if cat_of(x, by_name)]
    a_resto = sum(calcular_afinidad(prod["categoria"], c, af, cfg) for c in hist) / len(hist) if hist else a_ult
    s = round(a_ult * cfg["PESO_ULTIMO_PRODUCTO"] + a_resto * cfg["PESO_RESTO_HISTORIAL"])
    if bump_bonus:
        for comprado in cli["listaCompras"]:
            p = by_name.get(comprado)
            if p and prod["nombre"] in (p.get("orderBumps") or []):
                s = min(100, round(s * 1.15)); break
    return s

def _ancla(cli, prod_rec, af, cfg, by_name):
    best_af, best = 0, None
    for comprado in cli["listaCompras"]:
        cc = cat_of(comprado, by_name)
        if cc is None: continue
        a = calcular_afinidad(prod_rec["categoria"], cc, af, cfg)
        if a > best_af: best_af, best = a, comprado
    return best, best_af

def pick_tsl(cli, principales, af, cfg, by_name):
    cands = []
    for p in principales:
        if p["nombre"] in cli["listaCompras"]:
            continue
        cands.append((score(p, cli, af, cfg, by_name), p["id"], p))
    cands.sort(key=lambda x: (-x[0], x[1]))
    if not cands:
        return None
    sc, _, p = cands[0]
    anc, anc_af = _ancla(cli, p, af, cfg, by_name)
    return {"producto": p, "score": sc, "ancla": anc if anc_af >= cfg["TSL_ANCLA_MIN_SIMILARIDAD"] else None, "afinidadAncla": anc_af}

def pick_crosssell(cli, catalogo, af, cfg, by_name):
    cands = []
    for p in catalogo:
        if p["nombre"] in cli["listaCompras"]:
            continue
        sc = score(p, cli, af, cfg, by_name, bump_bonus=True)
        es_bump = any(p["nombre"] in ((by_name.get(c) or {}).get("orderBumps") or []) for c in cli["listaCompras"])
        cands.append({"p": p, "score": sc, "bump": es_bump})
    cands.sort(key=lambda x: (-x["score"], not x["bump"], x["p"]["id"]))
    pool = cands[: cfg["CANDIDATOS_INICIALES"]]
    res = []
    for c in cands:
        if c["bump"] and len(res) < cfg["PRODUCTOS_OUTPUT"]:
            res.append(c)
    for c in pool:
        if len(res) >= cfg["PRODUCTOS_OUTPUT"]:
            break
        if c in res:
            continue
        canibal = False
        for r in res:
            a = calcular_afinidad(c["p"]["categoria"], r["p"]["categoria"], af, cfg)
            if a >= cfg["UMBRAL_CANIBALIZACION"] and c["score"] - r["score"] < 15:
                canibal = True; break
        if not canibal:
            res.append(c)
    for c in pool:
        if len(res) >= cfg["PRODUCTOS_OUTPUT"]:
            break
        if c not in res:
            res.append(c)
    items = []
    for c in res[: cfg["PRODUCTOS_OUTPUT"]]:
        p, sc = c["p"], c["score"]
        if sc >= cfg["UMBRAL_DIRECTO"]: tipo = "directo"
        elif sc >= cfg["UMBRAL_RELACIONADO"]: tipo = "relacionado"
        elif sc >= cfg["UMBRAL_EXPLORATORIO"]: tipo = "exploratorio"
        else: tipo = "descubre"
        if tipo in ("directo", "relacionado"):
            desc, link = p.get("descripcionCorta", ""), p.get("linkCompra", "")
        else:
            desc = p.get("descripcionCuriosity", "") or p.get("descripcionCorta", "")
            link = p.get("linkLanding") or p.get("linkCompra", "")
        items.append({"afinidad": sc, "tipoMatch": tipo, "nombre": p["nombre"], "descripcion": desc, "link": link, "categoria": p["categoria"]})
    return items

def decide_mode(cli, tsl, cross, forced, n_principales, cfg):
    """Selección inteligente de modo (heurística determinista). AUTO por defecto.
    'tsl' solo permitido si hay >=2 principales."""
    if forced == "tsl" and n_principales >= 2 and tsl:
        return "tsl"
    if forced == "crosssell" and cross:
        return "crosssell"
    # AUTO
    tiene_bump = any(i["tipoMatch"] in ("directo",) for i in cross) or any(
        i for i in cross if i.get("afinidad", 0) >= cfg["UMBRAL_DIRECTO"])
    # señal: concentración fuerte en un principal con ancla -> TSL
    tsl_fuerte = bool(tsl) and tsl["score"] >= cfg["UMBRAL_RELACIONADO"] and tsl.get("ancla")
    n_relevantes = sum(1 for i in cross if i["afinidad"] >= cfg["UMBRAL_EXPLORATORIO"])
    if tiene_bump or n_relevantes >= 3:
        return "crosssell" if cross else "tsl"
    if tsl_fuerte:
        return "tsl"
    return "crosssell" if cross else ("tsl" if tsl else "none")
