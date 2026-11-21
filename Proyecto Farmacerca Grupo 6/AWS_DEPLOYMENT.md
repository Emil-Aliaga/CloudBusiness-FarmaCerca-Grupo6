# Guía de despliegue AWS — FarmaCerca Inventario

Esta guía usa una arquitectura sencilla y fácil de explicar en clase:

```text
Usuario
  ↓
Internet
  ↓
Amazon EC2 (Docker + FastAPI)
  ↓
Amazon RDS for PostgreSQL
```

Para una demo académica, esta arquitectura permite mostrar claramente la separación entre aplicación y base de datos centralizada.

## 1. Verificar el proyecto antes de subirlo

En la PC del desarrollador:

```bash
docker compose up --build
```

Abrir `http://localhost:8000` y comprobar Dashboard, Inventario, Detalle, Sucursales, Alertas y Transferencias.

También se puede ejecutar:

```bash
python tests/smoke_test.py
```

## 2. Subir el proyecto a GitHub

No subir:

- `.env`
- `farmacerca.db`
- `.venv/`

Sí subir:

- código
- templates y static
- `requirements.txt`
- `Dockerfile`
- `.env.example`
- esta guía

## 3. Crear Amazon RDS PostgreSQL

Crear una instancia PostgreSQL para la base centralizada.

Datos que necesitarás guardar:

- endpoint de RDS
- puerto, normalmente `5432`
- nombre de la base, por ejemplo `farmacerca`
- usuario
- contraseña

Recomendación: no abrir RDS a todo Internet. El Security Group de RDS debe aceptar PostgreSQL desde el Security Group de la instancia EC2 que ejecutará la aplicación.

Ejemplo de URL que usará FastAPI:

```text
postgresql+psycopg://USUARIO:CONTRASENA@RDS_ENDPOINT:5432/farmacerca
```

## 4. Crear Amazon EC2

Crear una instancia Linux y asociarle un Security Group.

Para una demo básica:

- SSH `22`: solo desde la IP del administrador.
- HTTP `80`: público para mostrar la web.
- HTTPS `443`: si luego configuran certificado/reverse proxy.

No es necesario exponer el puerto PostgreSQL de RDS al público.

## 5. Instalar Docker en EC2

Conectarse por SSH, instalar Docker según la distribución elegida y comprobar:

```bash
docker --version
```

Clonar el repositorio:

```bash
git clone URL_DEL_REPOSITORIO
cd farmacerca_cloud_ready
```

## 6. Crear las variables del entorno

Crear un archivo `.env` directamente en EC2 o suministrar las variables al contenedor.

Ejemplo:

```env
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASENA@RDS_ENDPOINT:5432/farmacerca
ENVIRONMENT=production
```

Nunca subir este archivo a GitHub.

## 7. Construir la imagen

```bash
docker build -t farmacerca .
```

## 8. Ejecutar la aplicación

Para una demo simple, publicar el puerto 8000 de FastAPI en el puerto HTTP 80 de EC2:

```bash
docker run -d \
  --name farmacerca \
  --restart unless-stopped \
  --env-file .env \
  -p 80:8000 \
  farmacerca
```

Abrir en el navegador:

```text
http://IP_PUBLICA_EC2
```

La primera vez que la aplicación se conecte a una base vacía, creará las tablas y cargará los datos demo.

## 9. Verificar salud

Abrir:

```text
http://IP_PUBLICA_EC2/health
```

En RDS debe responder algo similar a:

```json
{
  "status": "ok",
  "app": "FarmaCerca Inventario",
  "database": "postgresql"
}
```

## 10. Cómo explicar esta arquitectura en clase

**Antes:** cada local podría trabajar con información separada o desactualizada.

**Propuesta:** las sucursales acceden a una aplicación central en AWS y consultan una única base de datos de inventario.

```text
Miraflores ─┐
San Isidro ─┤
Surco ──────┼──> Aplicación en AWS ───> RDS PostgreSQL
La Molina ──┤
San Borja ──┘
```

Así, una actualización o transferencia queda disponible para las demás sedes desde el mismo sistema.

## 11. Mejoras posteriores (no necesarias para el MVP)

- Application Load Balancer + HTTPS.
- Route 53 para dominio.
- AWS Certificate Manager para certificado.
- Auto Scaling para múltiples instancias.
- CloudWatch para logs/monitorización.
- Secrets Manager o Parameter Store para secretos.
- S3/CloudFront para recursos estáticos si el proyecto creciera.

Estas mejoras son una evolución; no son necesarias para demostrar el MVP inicial.

## Referencias AWS oficiales

- Elastic Beanstalk para aplicaciones Python: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html
- Security Groups de EC2: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/creating-security-group.html
- Reglas de Security Group para servidores web: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html
- Solución de problemas de conexión a RDS PostgreSQL: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ConnectToPostgreSQLInstance.Troubleshooting.html


## 12. Verificación visual de que está en cloud

Cuando `ENVIRONMENT=production` y `DATABASE_URL` apunta a PostgreSQL, la interfaz mostrará en la parte superior/lateral:

```text
AWS / Producción
PostgreSQL / RDS
```

Esto ayuda en la exposición a demostrar que no solo cambió la URL: la misma aplicación está usando el entorno cloud configurado.

## 13. Reiniciar el escenario de demostración

La utilidad de desarrollo **reset_demo.bat** llama al endpoint de reinicio y recrea el inventario inicial. No aparece en la interfaz del usuario.

En un sistema productivo real esta función debería estar protegida o eliminada; aquí existe únicamente porque se trata de un MVP académico.
