from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from ..deps import current_user
from .. import models, storage
from ..core.hotmart import extract_products
from ..core.onboarding import catalog_draft, build_afinidad, DEFAULT_CONFIG
from ..core import catalog as C

router = APIRouter(prefix="/api/data", tags=["data"])

@router.post("/sales")
async def upload_sales(file: UploadFile = File(...), u: models.User = Depends(current_user)):
    content = await file.read()
    try:
        products = extract_products(content, file.filename)
    except Exception as e:
        raise HTTPException(422, f"No pude leer el archivo de ventas: {e}")
    storage.save_sales(u.email, content, file.filename)
    if not storage.exists(u.email, "entradas", "config.txt"):
        storage.write(u.email, DEFAULT_CONFIG, "entradas", "config.txt")
    created = False
    if not storage.exists(u.email, "entradas", "catalogo.json"):
        storage.write(u.email, catalog_draft(products), "entradas", "catalogo.json")
        created = True
    return {"product_count": len(products), "products": products,
            "catalog_created": created, "has_catalog": storage.exists(u.email, "entradas", "catalogo.json")}

@router.get("/catalog")
def download_catalog(u: models.User = Depends(current_user)):
    content = storage.read(u.email, "entradas", "catalogo.json") or '{"catalogo": []}'
    return Response(content, media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="catalogo.json"'})

class CatalogIn(BaseModel):
    content: str

@router.post("/catalog")
def upload_catalog(body: CatalogIn, u: models.User = Depends(current_user)):
    try:
        cat, principales, _ = C.load_catalogo(body.content)
    except Exception as e:
        raise HTTPException(422, f"El catálogo no es JSON válido: {e}")
    storage.write(u.email, body.content, "entradas", "catalogo.json")
    storage.write(u.email, build_afinidad(body.content), "entradas", "afinidad.txt")  # afinidad automática (oculta)
    sin_cat = [p["nombre"] for p in cat if not (p.get("categoria") or "").strip()]
    sin_land = [p["nombre"] for p in cat if p.get("esPrincipal") and not (p.get("linkLanding") or "").strip()]
    return {"ok": len(cat) > 0 and not sin_cat, "productos": len(cat), "principales": len(principales),
            "sin_categoria": sin_cat, "principales_sin_landing": sin_land}

@router.get("/status")
def status(u: models.User = Depends(current_user)):
    has_sales = storage.current_sales(u.email)[0] is not None
    has_cat = storage.exists(u.email, "entradas", "catalogo.json")
    productos = principales = 0; valid = False
    if has_cat:
        try:
            cat, pr, _ = C.load_catalogo(storage.read(u.email, "entradas", "catalogo.json"))
            productos = len(cat); principales = len(pr)
            valid = productos > 0 and all((p.get("categoria") or "").strip() for p in cat)
        except Exception:
            valid = False
    return {"has_sales": has_sales, "has_catalog": has_cat, "productos": productos,
            "principales": principales, "catalog_valid": valid,
            "has_resend": bool(u.resend_token_enc), "from_email": u.from_email}
