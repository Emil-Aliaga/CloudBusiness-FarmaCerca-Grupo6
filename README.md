# FarmaCerca Inventario

Sistema web de gestión de inventario multi-sucursal desarrollado para el proyecto final del curso **Cloud Business — Grupo 6**.

La solución busca centralizar la información de inventario de FarmaCerca, permitiendo consultar disponibilidad de productos entre sucursales, identificar situaciones críticas de stock y registrar transferencias de productos entre establecimientos.

El proyecto está preparado para funcionar tanto en un entorno local como en AWS sin modificar la lógica principal de la aplicación.

## Funcionalidades principales

### Dashboard
Vista general de la situación del inventario:

- Productos registrados.
- Unidades disponibles.
- Productos agotados.
- Productos con stock bajo.
- Productos próximos a vencer.
- Situación por sucursal.
- Movimientos recientes.

### Inventario
Permite:

- Buscar productos por nombre, SKU o categoría.
- Filtrar por sucursal.
- Filtrar por estado de inventario.
- Consultar stock disponible.
- Identificar productos agotados o con stock bajo.
- Actualizar cantidades.

### Detalle de producto
Muestra la situación de un producto en todas las sucursales:

- Stock por establecimiento.
- Stock mínimo.
- Estado de inventario.
- Fecha de vencimiento.
- Historial de movimientos.
- Recomendaciones de redistribución cuando existe falta de stock en una sucursal y disponibilidad en otra.

### Sucursales
Permite visualizar el estado del inventario de cada establecimiento y acceder directamente a los productos disponibles en una sede determinada.

### Transferencias
Permite registrar movimientos de productos entre establecimientos.

El sistema valida:

- Producto seleccionado.
- Sucursal de origen.
- Sucursal de destino.
- Cantidad disponible.
- Stock después de la transferencia.

Cada operación genera un registro de movimiento.

### Alertas
Identifica automáticamente:

- Productos agotados.
- Productos con stock bajo.
- Productos próximos a vencer.

Las alertas permiten acceder directamente al producto o iniciar una transferencia cuando corresponde.

---

## Arquitectura

La aplicación fue diseñada para utilizar la misma lógica tanto en desarrollo local como en AWS.

### Desarrollo local

```text
Usuario
   ↓
FastAPI
   ↓
SQLite
```

### Arquitectura cloud propuesta

```text
Usuarios / sucursales
        ↓
     Internet
        ↓
    Aplicación AWS
        ↓
      FastAPI
        ↓
Amazon RDS PostgreSQL
        ↓
Inventario centralizado
```

La conexión con la base de datos se configura mediante la variable de entorno `DATABASE_URL`.

---

## Tecnologías utilizadas

- Python
- FastAPI
- Jinja2
- SQLAlchemy
- SQLite para desarrollo local
- PostgreSQL para producción
- Amazon RDS
- HTML
- CSS
- JavaScript
- Docker

---


## Estructura del proyecto

```text
CloudBusiness-FarmaCerca-Grupo6/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── inventory.html
│   ├── product_detail.html
│   ├── branches.html
│   ├── transfers.html
│   └── alerts.html
│
├── static/
│   ├── styles.css
│   └── app.js
│
├── tests/
│   └── smoke_test.py
│
├── README.md
├── AWS_DEPLOYMENT.md
├── AWS_HANDOFF_CHECKLIST.md
├── DEMO_GUIDE.md
├── run_local.bat
├── run_local.sh
└── reset_demo.bat
```

---

## Repositorio

Proyecto desarrollado por el **Grupo 6 — Cloud Business**.

Repositorio:

https://github.com/Emil-Aliaga/CloudBusiness-FarmaCerca-Grupo6
