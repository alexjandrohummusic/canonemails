"""Generación de copy determinista (respaldo) + asuntos. Se usa cuando no hay
token de IA o como base. Portado del enfoque Lumetrix (plantilla por producto)."""
CONECTOR = "Ya diste un paso; el siguiente es este."
CIERRES = ["Míralo completo aquí:", "Descúbrelo aquí:", "Empieza hoy aquí:", "Léelo completo aquí:"]

def ficha_de(p: dict) -> dict:
    return {"nombre": p["nombre"], "curiosity": p.get("descripcionCuriosity", "") or "",
            "corta": p.get("descripcionCorta", "") or ""}

def tsl_body(p: dict, ancla: str | None, objetivo: int, tol: float = 0.10) -> str:
    f = ficha_de(p)
    hook = f["curiosity"] or f"Hay algo sobre «{f['nombre']}» que casi nadie te contó."
    ag = "Cada semana que sigues igual, el costo crece en silencio."
    if ancla:
        puente = f"Ya trabajaste en eso; el siguiente paso natural es {f['nombre']}."
    else:
        puente = f"Aquí entra {f['nombre']}."
    prom = f["corta"] or "Un método claro, específico y de bajo esfuerzo para lograrlo."
    prueba = "Otras personas ya lo aplican; los resultados varían, pero el enfoque funciona."
    urg = "No dejes que pase otra semana igual."
    secc = [hook, ag, puente, prom, prueba, urg]
    cuerpo = "\n\n".join(secc)
    lo, hi = int(objetivo * (1 - tol)), int(objetivo * (1 + tol))
    extras = [f["curiosity"], f["corta"], "Es simple, se hace en poco tiempo y se queda contigo.",
              "No necesitas ser experto: necesitas empezar."]
    i = 0
    while len(cuerpo) < lo and i < len(extras):
        if extras[i] and extras[i] not in cuerpo:
            secc.insert(len(secc) - 1, extras[i]); cuerpo = "\n\n".join(secc)
        i += 1
    if len(cuerpo) > hi:
        corte = cuerpo[:hi]
        u = max(corte.rfind(". "), corte.rfind(".\n"))
        if u > lo:
            cuerpo = corte[:u + 1]
    return cuerpo

def subjects_for(p: dict, n: int, maxlen: int) -> list:
    base = (p.get("descripcionCuriosity") or p["nombre"]).strip()
    nm = p["nombre"].split(":")[0].split("—")[0].strip()
    cands = [
        base[:maxlen],
        f"{{{{nombre}}}}, esto es para ti"[:maxlen],
        f"Lo que no sabías de {nm}"[:maxlen],
        f"El detalle que cambia todo en {nm}"[:maxlen],
        f"{{{{nombre}}}}, no lo dejes pasar"[:maxlen],
        f"Por qué {nm} importa más de lo que crees"[:maxlen],
    ]
    seen, out = set(), []
    for c in cands:
        c = c.replace("|", " ").strip()
        if c and c.lower() not in seen:
            seen.add(c.lower()); out.append(c)
        if len(out) >= n:
            break
    while len(out) < n:
        out.append(nm[:maxlen])
    return out[:n]
