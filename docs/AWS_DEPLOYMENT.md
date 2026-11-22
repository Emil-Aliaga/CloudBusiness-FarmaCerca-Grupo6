# Despliegue AWS — FarmaCerca

## Arquitectura objetivo

```text
Usuario
  │
  ▼
CloudFront
  │
  ▼
S3 (frontend estático)
  │
  │ HTTPS / fetch()
  ▼
App Runner (FastAPI)
  │
  │ VPC Connector
  ▼
RDS PostgreSQL
```

## 1. RDS PostgreSQL

1. Crea una base PostgreSQL llamada `farmacerca`.
2. Déjala en subredes privadas de la VPC.
3. Guarda usuario, contraseña, endpoint y puerto 5432.
4. El Security Group de RDS debe aceptar PostgreSQL **solo** desde el Security Group usado por el VPC Connector de App Runner.

La URL tendrá este formato:

```text
postgresql+psycopg://USER:PASSWORD@ENDPOINT:5432/farmacerca
```

## 2. App Runner — backend

1. Abre AWS App Runner → Create service.
2. Source: GitHub.
3. Repository: `CloudBusiness-FarmaCerca-Grupo6`.
4. Branch: `main`.
5. Source directory: `/backend`.
6. Configuration file: usar `apprunner.yaml` del repositorio.
7. Variables de entorno:

```text
ENVIRONMENT=production
SEED_DEMO_DATA=true
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@ENDPOINT:5432/farmacerca
CORS_ORIGINS=https://TU-DOMINIO-CLOUDFRONT.cloudfront.net
```

8. Networking → Outgoing network traffic → Custom VPC.
9. Crea/selecciona un VPC Connector con subredes que puedan alcanzar RDS y un Security Group apropiado.
10. Despliega.
11. Comprueba:

```text
https://TU-SERVICIO.awsapprunner.com/health
https://TU-SERVICIO.awsapprunner.com/docs
```

## 3. Frontend — configurar API

Antes de subir el frontend a S3, edita `frontend/config.js`:

```javascript
window.FARMACERCA_CONFIG = {
  API_BASE_URL: "https://TU-SERVICIO.awsapprunner.com"
};
```

## 4. S3 — frontend

1. Crea un bucket, por ejemplo `farmacerca-grupo6-frontend`.
2. Mantén **Block Public Access** activado.
3. Sube **el contenido de `frontend/`**, no la carpeta contenedora.
4. No necesitas habilitar el website endpoint si usarás CloudFront con OAC.

## 5. CloudFront

1. Crea una distribución.
2. Origin: el bucket S3 normal (no el website endpoint).
3. Configura Origin Access Control (OAC).
4. Default root object: `index.html`.
5. Viewer protocol policy: Redirect HTTP to HTTPS.
6. Aplica la bucket policy sugerida por CloudFront para permitir `s3:GetObject` desde la distribución.
7. Espera a que el estado sea Deployed y abre el dominio CloudFront.

## 6. Actualizar CORS

Una vez conozcas el dominio final de CloudFront, asegúrate de que App Runner tenga:

```text
CORS_ORIGINS=https://dxxxxxxxxxxxx.cloudfront.net
```

Si cambias la variable, vuelve a desplegar App Runner.

## 7. Prueba final

1. Abre el dominio CloudFront.
2. Dashboard debe cargar datos desde App Runner.
3. Busca Paracetamol en Inventario.
4. Edita un stock.
5. Realiza una transferencia.
6. Refresca y confirma que el cambio persiste en RDS.

## Nota sobre Docker

Este diseño **no requiere que el equipo mantenga Docker ni Dockerfile**. App Runner puede construir y ejecutar el backend directamente desde el código fuente Python del repositorio.
