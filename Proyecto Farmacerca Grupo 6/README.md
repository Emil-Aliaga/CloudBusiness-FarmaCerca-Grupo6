# FarmaCerca Inventario — MVP Cloud-ready v3

Prototipo académico para **Cloud Business**. La aplicación centraliza inventario de varias sucursales, permite consultar disponibilidad, detectar alertas y redistribuir stock entre locales.

La arquitectura está preparada para dos entornos sin cambiar la lógica de la aplicación:

- **Local:** FastAPI + SQLite.
- **AWS:** la misma app FastAPI + PostgreSQL en Amazon RDS usando `DATABASE_URL`.

## Pantallas incluidas

1. **Dashboard**: KPIs, alertas, stock por sucursal y movimientos recientes.
2. **Inventario**: búsqueda, filtros, estados de stock y edición de cantidades.
3. **Detalle de producto**: stock del mismo producto en todas las sucursales, alertas, trazabilidad y recomendación automática de redistribución.
4. **Sucursales**: resumen operativo de cada sede y acceso directo a su inventario.
5. **Transferencias**: mueve stock entre sedes con validaciones y registro de movimientos.
6. **Alertas**: agotados, stock bajo y productos próximos a vencer, con acciones rápidas.

Además, el menú muestra el **entorno activo** (Local/SQLite o AWS/PostgreSQL) y permite **restaurar el escenario demo** después de practicar cambios.

## Stack

- Python 3.12 recomendado
- FastAPI
- Jinja2
- SQLAlchemy
- SQLite para desarrollo
- PostgreSQL / Amazon RDS para cloud
- HTML + CSS + JavaScript
- Docker opcional

## Ejecutar en Windows

### Opción rápida

Haz doble clic en:

```text
run_local.bat
```

Después abre:

```text
http://127.0.0.1:8000
```

### Opción manual

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

La aplicación crea automáticamente `farmacerca.db` y carga datos demo si la base está vacía.

## Ejecutar con Docker

```bash
docker compose up --build
```

Abre:

```text
http://localhost:8000
```

## Configuración de base de datos

La app lee la variable de entorno `DATABASE_URL`.

### Local con SQLite

Si no defines ninguna variable, usa SQLite automáticamente. También puedes crear `.env` copiando `.env.example`:

```env
DATABASE_URL=sqlite:///./farmacerca.db
ENVIRONMENT=development
```

### AWS con PostgreSQL/RDS

Ejemplo:

```env
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASENA@RDS_ENDPOINT:5432/farmacerca
ENVIRONMENT=production
```

No subas `.env` ni contraseñas al repositorio. `.gitignore` ya excluye `.env`.

## Flujo recomendado para la exposición

1. Abrir **Dashboard**.
2. Entrar a **Inventario**.
3. Buscar `Paracetamol`.
4. Abrir **Detalle del producto**.
5. Mostrar que La Molina está agotada y otra sede tiene disponibilidad.
6. Pulsar **Transferir** hacia La Molina.
7. Elegir una sede origen y transferir unidades.
8. Volver al producto y comprobar que ambos stocks cambiaron.
9. Mostrar que la alerta se actualiza de acuerdo con el nuevo stock.
10. Si se desea repetir la presentación, ejecutar **reset_demo.bat** mientras la aplicación local está encendida.

## Entrega al compañero que desplegará AWS

Recomendado: subir esta carpeta a un repositorio privado/compartido de GitHub. El compañero debe recibir **todo el proyecto**, no solo `app.py`.

Archivos importantes:

```text
farmacerca_cloud_ready/
├── app.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── AWS_DEPLOYMENT.md
├── run_local.bat
├── templates/
├── static/
└── tests/
```

No es necesario enviar `farmacerca.db`: se genera automáticamente y contiene únicamente datos demo.

## Prueba rápida

Desde la raíz del proyecto:

```bash
python tests/smoke_test.py
```

Debe mostrar:

```text
Smoke test OK: navegación, detalle de producto y transferencia funcionando.
```

## Health check

```text
GET /health
```

Devuelve el estado de la aplicación y si está usando SQLite o PostgreSQL.

## Nota académica

Los productos, cantidades, precios y sucursales son datos demostrativos para presentar el concepto. No representan información operativa real de FarmaCerca.


## Mejoras de la versión 3

- Indicador visual del entorno activo: **Local + SQLite** o **AWS + PostgreSQL/RDS**.
- Métrica de **cobertura saludable** del inventario.
- Salud porcentual por sucursal.
- Recomendación automática de transferencia en el detalle de producto.
- Formulario de transferencia prellenado desde la recomendación.
- Utilidad local **reset_demo.bat** para restaurar el escenario inicial sin mostrar herramientas de prueba en la interfaz.
- Arquitectura visible en el Dashboard para facilitar la explicación del componente cloud.

Consulta también `DEMO_GUIDE.md` y `AWS_HANDOFF_CHECKLIST.md`.
