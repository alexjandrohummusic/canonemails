# LumetrixCore · Cañón de Correos (MVP)

SaaS de segmentación con IA y envío de campañas de email. Modelo **BYO-token**: cada
cliente usa **su** cuenta de Claude (IA) y **su** cuenta de Resend (envío). La plataforma
es un middleware de procesamiento; los prompts viven de nuestro lado.

Construido según el marco ganador: **monolito modular en Python/FastAPI**, salida única
consolidada por campaña, **selección inteligente de modo** (cross-sell / TSL / híbrido)
y motor de envío con pacing anti-spam.

## Qué hace (flujo del usuario)
1. Se registra e inicia sesión.
2. Guarda sus **tokens BYO** (Claude + Resend) — se cifran en reposo.
3. Define su **identidad de remitente** y verifica su **dominio** (SPF/DKIM/DMARC).
4. Completa su **catálogo** (las reglas/afinidad se autogeneran).
5. Sube su **archivo de ventas** (Hotmart) y pulsa **Generar**.
6. La IA decide por cliente el mejor formato; se produce **un solo archivo consolidado**.
7. Revisa el **preview de 3** y **envía**. El motor aplica el ritmo anti-spam.

## Arquitectura (módulos)
```
app/
  core/         motor de dominio (fuente de verdad única)
    catalog.py    carga/validación de catálogo, afinidad, config
    hotmart.py    parseo del export y construcción de clientes
    engine.py     afinidad, scoring, selección de modo, salida
    campaign.py   orquestador -> salida ÚNICA consolidada (bloques)
    ai.py         IA con token del usuario (BYO Claude), con respaldo
    copy.py       copy determinista de respaldo + asuntos
  emailing/
    themes.py     los 5 diseños seleccionables
    render.py     render dinámico (auto-detecta TSL vs cross-sell)
    sender.py     envío vía Resend (BYO)
    send_service.py  pacing anti-spam + idempotencia + supresión
  routers/      auth, account, campaigns, templates, domain
  workers/      Celery (envío en producción)
  static/       frontend (SPA vanilla)
data/           plantillas de configuración + ventas de ejemplo
```

## Correr en local (sin Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # y edita VAULT_KEY (ver abajo)
uvicorn app.main:app --reload --port 8000
# abre http://localhost:8000
```
Genera una clave de cifrado para el vault de tokens:
```bash
python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"
```
Pégala en `VAULT_KEY` del `.env`. Por defecto usa **SQLite** y `SEND_MODE=background`
(no requiere Redis) — ideal para probar. Para producción usa Postgres + `SEND_MODE=celery`.

## Correr con Docker (producción-like)
```bash
cp .env.example .env   # DATABASE_URL a postgres, SEND_MODE=celery
docker compose up --build
```
Levanta `web` (FastAPI), `worker` (Celery), `postgres` y `redis`.

## Prueba rápida
1. Regístrate en la UI. Se te crea un **catálogo de ejemplo** automáticamente.
2. En **Envío y dominio**, pega tus tokens de Claude y Resend, y tu correo de envío.
3. En **Nueva campaña**, sube `data/sample_sales.csv`, pulsa **Generar** y revisa el preview.
4. (Con tokens reales y dominio verificado) pulsa **Enviar**.

También: `make test` corre la prueba del motor sobre los datos de ejemplo.

## Pacing anti-spam (variables de configuración)
En `.env`: `WARMUP_MAX_PER_HOUR`, `WARMUP_MAX_PER_DAY`, `SEND_MIN_DELAY_SEC`,
`SEND_MAX_DELAY_SEC`, `SEND_PAUSE_EVERY`, `SEND_PAUSE_SECONDS`. Empieza conservador y sube.

## Suscripción (Hotmart)
El cobro recurrente lo gestiona Hotmart. Endpoint `POST /api/account/hotmart/webhook`
activa/suspende la cuenta según el evento (`PURCHASE_APPROVED`, `SUBSCRIPTION_CANCELLATION`,
`PURCHASE_REFUNDED`).

## Estado y siguientes pasos (MVP → producción)
- **Listo:** auth, tokens cifrados BYO, catálogo/afinidad/config, motor (paridad con el
  algoritmo actual), selección de modo, salida única, render dinámico con 5 plantillas,
  preview de 3, envío con pacing, verificador de DNS, webhook Hotmart.
- **Por endurecer (según el plan de fases):** multi-tenant con RLS, fetch de landings con
  render headless, guardarraíles de contenido, warm-up adaptativo, dashboard de
  entregabilidad (webhooks de Resend), pruebas de las 5 plantillas en clientes de correo,
  onboarding asistido para categorías nuevas.

> MVP funcional para validar el circuito completo BYO. No enviar a producción sin dominio
> verificado y sin respetar el ritmo de warm-up.
