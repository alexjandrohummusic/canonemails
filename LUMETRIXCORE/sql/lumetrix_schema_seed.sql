-- =====================================================================
-- LumetrixCore · Cañón de Correos
-- DDL de entidades + datos de ejemplo (10 registros por entidad)
-- ---------------------------------------------------------------------
-- Motor objetivo : PostgreSQL 16 (compatible con el docker-compose del proyecto)
-- Fuente         : app/models.py  (User, Campaign, Recipient, Suppression, ConfigFile)
-- Orden          : se crean/insertan respetando las llaves foráneas
--                  users -> campaigns -> recipients
--                  users -> suppression
--                  users -> config_files
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Limpieza (orden inverso de dependencias)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS recipients   CASCADE;
DROP TABLE IF EXISTS config_files CASCADE;
DROP TABLE IF EXISTS suppression  CASCADE;
DROP TABLE IF EXISTS campaigns    CASCADE;
DROP TABLE IF EXISTS users        CASCADE;

-- =====================================================================
-- DDL
-- =====================================================================

-- users -----------------------------------------------------------------
CREATE TABLE users (
    id                    SERIAL       PRIMARY KEY,
    email                 VARCHAR(255) NOT NULL,
    name                  VARCHAR(120) NOT NULL DEFAULT '',
    password_hash         VARCHAR(255) NOT NULL,
    -- BYO tokens (en el MVP el "cifrado" es no-op; se guardan en texto plano)
    claude_token_enc      TEXT         NOT NULL DEFAULT '',
    resend_token_enc      TEXT         NOT NULL DEFAULT '',
    -- Identidad de remitente
    from_name             VARCHAR(120) NOT NULL DEFAULT '',
    from_email            VARCHAR(255) NOT NULL DEFAULT '',
    template              VARCHAR(40)  NOT NULL DEFAULT 'minimal',
    -- Suscripción (Hotmart)
    subscription_status   VARCHAR(30)  NOT NULL DEFAULT 'active',
    hotmart_subscriber_id VARCHAR(120) NOT NULL DEFAULT '',
    created_at            TIMESTAMP    NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

-- campaigns -------------------------------------------------------------
CREATE TABLE campaigns (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users (id),
    status      VARCHAR(30) NOT NULL DEFAULT 'generated',  -- generated|sending|paused|done|error
    mode        VARCHAR(20) NOT NULL DEFAULT 'auto',       -- auto|tsl|crosssell
    blocks_json TEXT        NOT NULL DEFAULT '[]',          -- salida ÚNICA consolidada
    report_json TEXT        NOT NULL DEFAULT '{}',
    total       INTEGER     NOT NULL DEFAULT 0,
    sent        INTEGER     NOT NULL DEFAULT 0,
    failed      INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMP   NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_campaigns_user_id ON campaigns (user_id);

-- recipients ------------------------------------------------------------
CREATE TABLE recipients (
    id          SERIAL       PRIMARY KEY,
    campaign_id INTEGER      NOT NULL REFERENCES campaigns (id),
    email       VARCHAR(255) NOT NULL,
    state       VARCHAR(20)  NOT NULL DEFAULT 'queued',     -- queued|sent|failed|skipped
    provider_id VARCHAR(120) NOT NULL DEFAULT ''
);
CREATE INDEX ix_recipients_campaign_id ON recipients (campaign_id);
CREATE INDEX ix_recipients_email       ON recipients (email);

-- suppression -----------------------------------------------------------
CREATE TABLE suppression (
    id      SERIAL       PRIMARY KEY,
    user_id INTEGER      NOT NULL REFERENCES users (id),
    email   VARCHAR(255) NOT NULL,
    reason  VARCHAR(40)  NOT NULL DEFAULT 'unsubscribe'      -- unsubscribe|bounce|complaint
);
CREATE INDEX ix_suppression_user_id ON suppression (user_id);
CREATE INDEX ix_suppression_email   ON suppression (email);

-- config_files ----------------------------------------------------------
CREATE TABLE config_files (
    id      SERIAL      PRIMARY KEY,
    user_id INTEGER     NOT NULL REFERENCES users (id),
    kind    VARCHAR(30) NOT NULL,                            -- catalogo|afinidad|config
    content TEXT        NOT NULL DEFAULT ''
);
CREATE INDEX ix_config_files_user_id ON config_files (user_id);

-- =====================================================================
-- DATOS DE EJEMPLO (10 por entidad)
-- =====================================================================

-- users -----------------------------------------------------------------
-- password_hash de ejemplo con formato pbkdf2_sha256 (no son hashes reales usables)
INSERT INTO users
    (id, email, name, password_hash, claude_token_enc, resend_token_enc,
     from_name, from_email, template, subscription_status, hotmart_subscriber_id, created_at)
VALUES
   -- (1,  'admin@lumetrixcore.com', 'Admin',        'pbkdf2_sha256$29000$seed0001$aWRhZG1pbg==', '', '',                 'Lumetrix',       'hola@lumetrixcore.com',  'minimal',     'active',    'HM-0001', '2026-06-01 09:00:00'),
    (2,  'ana.lopez@gmail.com',    'Ana López',    'pbkdf2_sha256$29000$seed0002$aWRhbmExMDI=', 'sk-ant-ana',  're_ana_123',     'Bienestar Ana',  'hola@bienestarana.com',  'editorial',   'active',    'HM-0002', '2026-06-02 10:15:00'),
    (3,  'beto.ruiz@hotmail.com',  'Beto Ruiz',    'pbkdf2_sha256$29000$seed0003$aWRiZXRvMTAz', '',            're_beto_456',    'Reto Metabolico','envios@retobeto.com',    'wellness',    'active',    'HM-0003', '2026-06-03 11:30:00'),
    (4,  'carla.diaz@outlook.com', 'Carla Díaz',   'pbkdf2_sha256$29000$seed0004$aWRjYXJsYTA0', '',            '',               'Carla Academy',  'info@carladiaz.com',     'corporativo', 'suspended', 'HM-0004', '2026-06-04 08:45:00'),
    (5,  'dora.mena@yahoo.com',    'Dora Mena',    'pbkdf2_sha256$29000$seed0005$aWRkb3JhMTA1', '',            're_dora_789',    'Dora Calma',     'hola@doracalma.com',     'bold',        'active',    'HM-0005', '2026-06-05 14:20:00'),
    (6,  'emilio.sanz@gmail.com',  'Emilio Sanz',  'pbkdf2_sha256$29000$seed0006$aWRlbWlsMTA2', 'sk-ant-emi',  're_emilio_321',  'Emilio IA',      'cursos@emilioia.com',    'minimal',     'active',    'HM-0006', '2026-06-06 16:05:00'),
    (7,  'fernanda.gil@gmail.com', 'Fernanda Gil', 'pbkdf2_sha256$29000$seed0007$aWRmZXJuMTA3', '',            '',               'Fer Wellness',   'hola@ferwellness.com',   'wellness',    'suspended', 'HM-0007', '2026-06-07 09:10:00'),
    (8,  'gustavo.rey@gmail.com',  'Gustavo Rey',  'pbkdf2_sha256$29000$seed0008$aWRndXN0MTA4', '',            're_gus_654',     'Rey Editorial',  'news@gustavorey.com',    'editorial',   'active',    'HM-0008', '2026-06-08 12:40:00'),
    (9,  'helena.cruz@gmail.com',  'Helena Cruz',  'pbkdf2_sha256$29000$seed0009$aWRoZWxlMTA5', 'sk-ant-hel',  're_helena_987',  'Helena Corp',    'contacto@helenacruz.com','corporativo', 'active',    'HM-0009', '2026-06-09 15:55:00'),
    (10, 'ivan.mora@gmail.com',    'Iván Mora',    'pbkdf2_sha256$29000$seed0010$aWRpdmFuMTAx', '',            're_ivan_147',    'Ivan Bold',      'hola@ivanmora.com',      'bold',        'active',    'HM-0010', '2026-06-10 18:25:00');

-- campaigns -------------------------------------------------------------
INSERT INTO campaigns
    (id, user_id, status, mode, blocks_json, report_json, total, sent, failed, created_at)
VALUES
    --(1,  1,  'done',      'auto',      '[{"type": "tsl", "email": "cliente1@example.com", "nombre": "Cliente"}]',       '{"clientes": 5, "bloques": 5, "distribucion_modo": {"tsl": 3, "crosssell": 2}}',   5,   5,   0, '2026-06-11 09:00:00'),
    (2,  2,  'sending',   'auto',      '[{"type": "crosssell", "email": "cliente2@example.com", "nombre": "Cliente"}]', '{"clientes": 120, "bloques": 118, "distribucion_modo": {"auto": 118}}',            120, 45,  2, '2026-06-12 10:00:00'),
    (3,  3,  'generated', 'crosssell', '[{"type": "crosssell", "email": "cliente3@example.com", "nombre": "Cliente"}]', '{"clientes": 30, "bloques": 30, "distribucion_modo": {"crosssell": 30}}',          30,  0,   0, '2026-06-13 11:00:00'),
    (4,  4,  'paused',    'auto',      '[{"type": "tsl", "email": "cliente4@example.com", "nombre": "Cliente"}]',       '{"clientes": 500, "bloques": 495, "distribucion_modo": {"tsl": 200, "crosssell": 295}}', 500, 200, 5, '2026-06-14 08:30:00'),
    (5,  5,  'done',      'tsl',       '[{"type": "tsl", "email": "cliente5@example.com", "nombre": "Cliente"}]',       '{"clientes": 12, "bloques": 12, "distribucion_modo": {"tsl": 12}}',                 12,  11,  1, '2026-06-15 14:00:00'),
    (6,  6,  'error',     'auto',      '[]',                                                                            '{"clientes": 0, "bloques": 0, "distribucion_modo": {}}',                            0,   0,   0, '2026-06-16 16:00:00'),
    (7,  7,  'generated', 'tsl',       '[{"type": "tsl", "email": "cliente7@example.com", "nombre": "Cliente"}]',       '{"clientes": 8, "bloques": 8, "distribucion_modo": {"tsl": 8}}',                    8,   0,   0, '2026-06-17 09:00:00'),
    (8,  8,  'done',      'crosssell', '[{"type": "crosssell", "email": "cliente8@example.com", "nombre": "Cliente"}]', '{"clientes": 60, "bloques": 60, "distribucion_modo": {"crosssell": 60}}',          60,  60,  0, '2026-06-18 12:00:00'),
    (9,  9,  'sending',   'auto',      '[{"type": "tsl", "email": "cliente9@example.com", "nombre": "Cliente"}]',       '{"clientes": 90, "bloques": 89, "distribucion_modo": {"auto": 89}}',                90,  30,  1, '2026-06-19 15:00:00'),
    (10, 10, 'done',      'auto',      '[{"type": "crosssell", "email": "cliente10@example.com", "nombre": "Cliente"}]','{"clientes": 15, "bloques": 15, "distribucion_modo": {"tsl": 6, "crosssell": 9}}', 15,  14,  1, '2026-06-20 18:00:00');

-- recipients ------------------------------------------------------------
INSERT INTO recipients
    (id, campaign_id, email, state, provider_id)
VALUES
    --(1,  1,  'cliente1@example.com',  'sent',    're_msg_0001'),
    --(2,  1,  'cliente1b@example.com', 'sent',    're_msg_0002'),
    (3,  2,  'cliente2@example.com',  'sent',    're_msg_0003'),
    (4,  2,  'cliente2b@example.com', 'failed',  ''),
    (5,  3,  'cliente3@example.com',  'queued',  ''),
    (6,  4,  'cliente4@example.com',  'sent',    're_msg_0006'),
    (7,  4,  'cliente4b@example.com', 'skipped', ''),
    (8,  5,  'cliente5@example.com',  'sent',    're_msg_0008'),
    (9,  8,  'cliente8@example.com',  'sent',    're_msg_0009'),
    (10, 9,  'cliente9@example.com',  'queued',  '');

-- suppression -----------------------------------------------------------
INSERT INTO suppression
    (id, user_id, email, reason)
VALUES
    --(1,  1,  'baja1@example.com',     'unsubscribe'),
    --(2,  1,  'rebote1@example.com',   'bounce'),
    (3,  2,  'baja2@example.com',     'unsubscribe'),
    (4,  2,  'queja2@example.com',    'complaint'),
    (5,  3,  'rebote3@example.com',   'bounce'),
    (6,  4,  'baja4@example.com',     'unsubscribe'),
    (7,  5,  'queja5@example.com',    'complaint'),
    (8,  6,  'rebote6@example.com',   'bounce'),
    (9,  8,  'baja8@example.com',     'unsubscribe'),
    (10, 9,  'rebote9@example.com',   'bounce');

-- config_files ----------------------------------------------------------
INSERT INTO config_files
    (id, user_id, kind, content)
VALUES
    --(1,  1, 'catalogo', '{"catalogo": [{"id": 1, "nombre": "Producto demo", "esPrincipal": true, "categoria": "Salud/Sistema Nervioso"}]}'),
    --(2,  1, 'afinidad', E'[FAMILIAS]\nSalud\nBienestar\nEducacion\n\n[SUBCATEGORIAS]\nSalud: Sistema Nervioso, Metabolismo\n'),
    (3,  1, 'config',   E'PESO_ULTIMO_PRODUCTO=0.7\nPESO_RESTO_HISTORIAL=0.3\nPRODUCTOS_OUTPUT=4\n'),
    (4,  2, 'catalogo', '{"catalogo": [{"id": 1, "nombre": "Metodo Calma", "esPrincipal": true, "categoria": "Salud/Sistema Nervioso"}]}'),
    (5,  2, 'afinidad', E'[FAMILIAS]\nSalud\n\n[WELLNESS]\nSalud\n'),
    (6,  2, 'config',   E'UMBRAL_DIRECTO=75\nUMBRAL_RELACIONADO=50\nUMBRAL_EXPLORATORIO=30\n'),
    (7,  3, 'catalogo', '{"catalogo": [{"id": 1, "nombre": "Interruptor Metabolico 35+", "esPrincipal": true, "categoria": "Salud/Metabolismo"}]}'),
    (8,  3, 'config',   E'TSL_LONGITUD_OBJETIVO=900\nTSL_ANCLA_MIN_SIMILARIDAD=40\n'),
    (9,  4, 'catalogo', '{"catalogo": [{"id": 1, "nombre": "IA Desde Cero", "esPrincipal": true, "categoria": "Educacion/Inteligencia Artificial"}]}'),
    (10, 5, 'catalogo', '{"catalogo": [{"id": 1, "nombre": "Audio de respiracion guiada", "esPrincipal": false, "categoria": "Bienestar/Somatico"}]}');

-- ---------------------------------------------------------------------
-- Sincronizar las secuencias SERIAL con los ids insertados manualmente
-- ---------------------------------------------------------------------
SELECT setval('users_id_seq',        (SELECT MAX(id) FROM users));
SELECT setval('campaigns_id_seq',    (SELECT MAX(id) FROM campaigns));
SELECT setval('recipients_id_seq',   (SELECT MAX(id) FROM recipients));
SELECT setval('suppression_id_seq',  (SELECT MAX(id) FROM suppression));
SELECT setval('config_files_id_seq', (SELECT MAX(id) FROM config_files));

COMMIT;
