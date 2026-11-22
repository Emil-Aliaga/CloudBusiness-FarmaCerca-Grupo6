# FarmaCerca — Inventario centralizado

Proyecto del Grupo 6 para Cloud Business. La aplicación está separada en **frontend** y **backend** para desplegar cada capa con servicios administrados de AWS.

## Arquitectura

```text
Internet
   │
   ▼
Amazon CloudFront
   │
   ▼
Amazon S3
FRONTEND
HTML / CSS / JavaScript
   │
   │ HTTPS API
   ▼
AWS App Runner
BACKEND
FastAPI
   │
   │ DATABASE_URL
   ▼
Amazon RDS
PostgreSQL
```

## Estructura

```text
frontend/
  index.html
  inventory.html
  branches.html
  transfers.html
  alerts.html
  product.html
  styles.css
  app.js
  config.js

backend/
  app.py
  requirements.txt
  apprunner.yaml
  .env.example
  tests/

docs/
  AWS_DEPLOYMENT.md
```

## Ejecutar todo en local — Windows

Desde la raíz:

```powershell
.\run_local.bat
```

Después abre:

- Frontend: http://127.0.0.1:5500
- API: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs

El backend usa SQLite automáticamente en local.

## Ejecutar por separado

### Backend

```powershell
cd backend
.\run_local.bat
```

### Frontend

```powershell
cd frontend
.\run_local.bat
```

## AWS

- `frontend/` se sube a **Amazon S3** y se sirve por **CloudFront**.
- `backend/` se despliega desde GitHub en **AWS App Runner** usando el source directory `/backend`.
- App Runner se conecta a **Amazon RDS PostgreSQL** mediante un VPC Connector.
- El frontend apunta a la URL HTTPS de App Runner mediante `frontend/config.js`.

Consulta `docs/AWS_DEPLOYMENT.md` para los pasos completos.
