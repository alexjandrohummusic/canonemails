import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .db import init_db
from .seed import seed_admin
from .routers import auth, account, campaigns, templates, domain, data

app = FastAPI(title="LumetrixCore · Cañón de Correos", version="0.1.0")
init_db()  # asegura tablas al importar (idempotente)

@app.on_event("startup")
def _startup():
    init_db()
    seed_admin()

app.include_router(auth.router)
app.include_router(account.router)
app.include_router(campaigns.router)
app.include_router(templates.router)
app.include_router(domain.router)
app.include_router(data.router)


from fastapi.requests import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})

@app.get("/api/health")
def health():
    return {"ok": True}

_STATIC = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_STATIC), name="static")

@app.get("/")
def index():
    return FileResponse(os.path.join(_STATIC, "index.html"))
