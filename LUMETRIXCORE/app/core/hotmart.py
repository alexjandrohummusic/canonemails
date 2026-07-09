"""Parseo del export de Hotmart (XLS/XLSX/CSV) y construcción de clientes."""
import io, pandas as pd

PLACEHOLDERS = {"", "nan", "none", "(none)", "-", "sin email", "null"}

def email_valido(e) -> bool:
    s = str(e).strip().lower()
    if s in PLACEHOLDERS or "@" not in s:
        return False
    dom = s.split("@")[-1]
    return "." in dom and dom != ""

def cap_nombre(n) -> str:
    n = " ".join(str(n).split())
    if not n:
        return "Hola"
    f = n.split()[0]
    return f.upper() if len(f) <= 1 else f[:1].upper() + f[1:].lower()

def _read(content: bytes, filename: str) -> pd.DataFrame:
    fn = (filename or "").lower()
    if fn.endswith((".xls", ".xlsx")):
        return pd.read_excel(io.BytesIO(content))
    return pd.read_csv(io.BytesIO(content), sep=None, engine="python")

def build_clients(content: bytes, filename: str, by_name: dict, cfg: dict, suppression: set):
    df = _read(content, filename)
    cols = {c.lower().strip(): c for c in df.columns}
    def col(*names):
        for n in names:
            if n in cols: return cols[n]
        for n in names:
            for k, orig in cols.items():
                if n in k: return orig
        return None
    c_email = col("email del comprador", "email", "correo")
    c_nom = col("comprador(a)", "comprador", "nombre del comprador", "nombre", "name")
    c_prod = col("producto", "product")
    c_fecha = col("fecha de la transacción", "fecha", "date")
    c_estatus = col("estatus de la transacción", "estatus", "estado", "status")
    c_herram = col("herramienta de venta", "herramienta")
    c_ticket = col("valor de compra con impuestos", "valor", "precio")
    c_moneda = col("moneda de compra", "moneda", "currency")
    if c_email is None or c_prod is None:
        raise ValueError("No se encontró columna de email o producto en el archivo.")
    if c_fecha:
        df["_f"] = pd.to_datetime(df[c_fecha], errors="coerce", dayfirst=True)
    else:
        df["_f"] = pd.NaT
    if c_estatus and cfg["ESTATUS_VALIDOS"]:
        df = df[df[c_estatus].astype(str).str.strip().isin(cfg["ESTATUS_VALIDOS"])]

    tmp = {}
    excl_email = excl_supp = 0
    warn = set()
    for _, r in df.iterrows():
        e = str(r[c_email]).strip()
        if not email_valido(e):
            excl_email += 1; continue
        k = e.lower()
        if k in suppression:
            excl_supp += 1; continue
        prod = str(r[c_prod]).strip()
        if prod not in by_name:
            warn.add(prod)
        es_bump = c_herram is not None and str(r[c_herram]).strip().lower() == "producto order bump"
        ticket = ""
        if c_ticket is not None:
            mon = str(r[c_moneda]).strip() if c_moneda else ""
            ticket = f"{r[c_ticket]} {mon}".strip()
        d = tmp.setdefault(k, {"email": e, "nombre": r[c_nom] if c_nom else "", "compras": [], "cabezas": []})
        d["compras"].append({"producto": prod, "fecha": r["_f"], "ticket": ticket})
        if not es_bump:
            d["cabezas"].append({"producto": prod, "fecha": r["_f"], "ticket": ticket})

    clientes = []
    for k, d in tmp.items():
        cab = d["cabezas"] or d["compras"]
        cab = sorted(cab, key=lambda x: (x["fecha"] is not None, x["fecha"]), reverse=True)
        principal = cab[0]["producto"] if cab else ""
        ticket = cab[0]["ticket"] if cab else ""
        compras = [c["producto"] for c in d["compras"]]
        historial = [n for n in dict.fromkeys(compras) if n != principal]
        clientes.append({
            "email": d["email"], "nombre": cap_nombre(d["nombre"]),
            "productoPrincipal": principal, "ticketPrincipal": ticket,
            "listaCompras": compras, "historial": historial,
        })
    return clientes, {"excl_email": excl_email, "excl_supp": excl_supp, "warn": sorted(warn)}


def extract_products(content: bytes, filename: str):
    """Devuelve la lista de nombres de producto únicos del archivo de ventas."""
    df = _read(content, filename)
    cols = {c.lower().strip(): c for c in df.columns}
    c_prod = None
    for n in ("producto", "product"):
        if n in cols: c_prod = cols[n]; break
    if c_prod is None:
        for k, o in cols.items():
            if "producto" in k: c_prod = o; break
    if c_prod is None:
        raise ValueError("No se encontró la columna 'Producto' en el archivo.")
    return sorted({str(x).strip() for x in df[c_prod].dropna() if str(x).strip()})
