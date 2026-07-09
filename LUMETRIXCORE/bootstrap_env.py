"""Crea .env con una APP_SECRET generada (idempotente). Sin cifrado de tokens por ahora."""
import os, secrets
if os.path.exists(".env"):
    print(".env ya existe (no se toca)"); raise SystemExit(0)
tmpl = open(".env.example", encoding="utf-8").read()
tmpl = tmpl.replace("APP_SECRET=cambia-esto-por-una-cadena-larga-y-secreta",
                    f"APP_SECRET={secrets.token_urlsafe(48)}")
open(".env", "w", encoding="utf-8").write(tmpl)
print(".env creado con APP_SECRET generado")
