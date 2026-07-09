"""Orquestador de campaña: de archivo de ventas -> salida ÚNICA consolidada
(bloques TSL y/o cross-sell entremezclados). Modo AUTO por defecto."""
from collections import Counter, defaultdict
from . import catalog as C, engine as E, copy as CP, ai
from .hotmart import build_clients

def generate(sales_bytes, sales_name, catalogo_txt, afinidad_txt, config_txt,
             suppression: set, claude_token: str = "", forced_mode: str = "auto"):
    cfg = C.load_config(config_txt)
    af = C.load_afinidad(afinidad_txt)
    cat, principales, by_name = C.load_catalogo(catalogo_txt)

    nuevas = C.validar_categorias(cat, af)
    if nuevas:
        return {"error": "categorias_nuevas", "detalle": [
            {"categoria": c, "producto": n, "id": i} for c, n, i in nuevas]}

    clientes, stats = build_clients(sales_bytes, sales_name, by_name, cfg, suppression)
    n_principales = len(principales)

    # decidir modo y armar bloque por cliente
    blocks, dist_mode, dist_prod = [], Counter(), Counter()
    interes_group = defaultdict(list)  # (mode, producto) -> indices, para round-robin de asuntos
    for cli in clientes:
        tsl = E.pick_tsl(cli, principales, af, cfg, by_name)
        cross = E.pick_crosssell(cli, cat, af, cfg, by_name)
        mode = E.decide_mode(cli, tsl, cross, forced_mode, n_principales, cfg)
        if mode == "tsl" and tsl:
            p = tsl["producto"]
            body = ai.write_tsl(claude_token, {"nombre": p["nombre"],
                    "curiosity": p.get("descripcionCuriosity", ""), "corta": p.get("descripcionCorta", "")},
                    tsl["ancla"], cfg["TSL_LONGITUD_OBJETIVO"]) or \
                   CP.tsl_body(p, tsl["ancla"], cfg["TSL_LONGITUD_OBJETIVO"], cfg["TSL_TOLERANCIA_LONGITUD"])
            blk = {"type": "tsl", "email": cli["email"], "nombre": cli["nombre"],
                   "producto": p["nombre"], "categoria": p["categoria"],
                   "cuerpo": body, "url": p.get("linkLanding") or p.get("linkCompra", ""),
                   "ancla": tsl["ancla"] or "ninguna", "afinidadAncla": tsl["afinidadAncla"],
                   "score": tsl["score"], "asunto": ""}
            interes_group[("tsl", p["nombre"])].append(len(blocks))
            dist_prod[p["nombre"]] += 1
        elif mode == "crosssell" and cross:
            blk = {"type": "crosssell", "email": cli["email"], "nombre": cli["nombre"],
                   "productoPrincipal": cli["productoPrincipal"], "ticket": cli["ticketPrincipal"],
                   "items": cross, "asunto": ""}
            top = max(cross, key=lambda x: x["afinidad"])
            interes_group[("cross", top["nombre"])].append(len(blocks))
            dist_prod[top["nombre"]] += 1
        else:
            continue  # cliente sin oferta disponible
        dist_mode[mode] += 1
        blocks.append(blk)

    # asuntos por interés (round-robin) — respaldo determinista o IA
    subj_cache = {}
    for (kind, prod_name), idxs in interes_group.items():
        p = by_name.get(prod_name)
        if not p:
            continue
        if prod_name not in subj_cache:
            subs = ai.write_subjects(claude_token, {"nombre": prod_name,
                    "curiosity": p.get("descripcionCuriosity", "")}, cfg["ASUNTOS_POR_INTERES"],
                    cfg["ASUNTO_MAX_CARACTERES"]) or CP.subjects_for(p, cfg["ASUNTOS_POR_INTERES"], cfg["ASUNTO_MAX_CARACTERES"])
            subj_cache[prod_name] = subs
        subs = subj_cache[prod_name]
        for i, bi in enumerate(sorted(idxs, key=lambda j: blocks[j]["email"])):
            blocks[bi]["asunto"] = subs[i % len(subs)]

    report = {
        "clientes": len(clientes), "bloques": len(blocks),
        "excluidos_email": stats["excl_email"], "excluidos_supresion": stats["excl_supp"],
        "warn_desconocidos": stats["warn"], "principales": n_principales,
        "distribucion_modo": dict(dist_mode),
        "distribucion_producto": dict(dist_prod.most_common()),
        "sin_oferta": len(clientes) - len(blocks),
    }
    return {"blocks": blocks, "report": report}
