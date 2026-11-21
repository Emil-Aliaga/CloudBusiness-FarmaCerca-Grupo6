# Checklist para entregar el proyecto al responsable de AWS

## Archivos que debe recibir

- `app.py`
- `templates/`
- `static/`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `.gitignore`
- `AWS_DEPLOYMENT.md`
- `tests/`

No enviar ni subir al repositorio:

- `.env`
- contraseñas
- `farmacerca.db`
- `.venv/`

## Prueba antes del traspaso

En local:

```bash
python tests/smoke_test.py
```

Debe terminar con:

```text
Smoke test OK: navegación, detalle de producto y transferencia funcionando.
```

## Variables que AWS deberá configurar

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASENA@RDS_ENDPOINT:5432/farmacerca
```

## Resultado esperado después del despliegue

1. La IP/URL pública carga el Dashboard.
2. `/health` devuelve `database: postgresql`.
3. La interfaz muestra `AWS / Producción` y `PostgreSQL / RDS`.
4. Buscar `Paracetamol` funciona.
5. Se puede realizar una transferencia.
6. El cambio persiste al recargar la web.
7. El Security Group de RDS no está abierto a todo Internet.

## Si algo falla

Revisar en este orden:

1. `DATABASE_URL`.
2. Conectividad EC2 → RDS por puerto 5432.
3. Security Groups.
4. Logs del contenedor.
5. `http://IP_PUBLICA/health`.
