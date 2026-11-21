# Guía de demo — FarmaCerca Inventario

Duración sugerida: **2 a 4 minutos**.

## 1. Dashboard

Abrir `/`.

Explicar:

> “Este dashboard centraliza el inventario de las sucursales piloto. Podemos ver rápidamente cuántos productos están saludables, con stock bajo, agotados o próximos a vencer.”

Señalar también el indicador de entorno:

- Local + SQLite durante desarrollo.
- AWS / Producción + PostgreSQL/RDS después del despliegue.

## 2. Buscar Paracetamol

Entrar a **Inventario** y buscar:

```text
Paracetamol
```

Explicar:

> “En lugar de llamar a cada local, podemos consultar el mismo producto en todas las sedes desde una sola pantalla.”

## 3. Abrir detalle del producto

Pulsar **Ver**.

Mostrar:

- La Molina: agotado.
- Otras sedes: stock disponible.
- Recomendación automática de redistribución.

Explicar:

> “El sistema identifica una sede crítica y una sede con excedente para proponer una redistribución antes de realizar una nueva compra.”

## 4. Crear transferencia

Pulsar **Crear transferencia**.

El formulario debe llegar prellenado con:

- producto,
- origen sugerido,
- destino crítico,
- cantidad sugerida.

Confirmar la transferencia.

## 5. Mostrar el resultado

Volver al producto.

Explicar:

> “La operación actualiza automáticamente el stock de origen y destino y además queda registrada para trazabilidad.”

Después entrar a **Alertas** para mostrar cómo cambia la prioridad.

## 6. Conectar con Cloud Business

Cerrar con:

> “El prototipo funciona primero de forma local con SQLite. La misma aplicación se puede desplegar en AWS y conectarse a Amazon RDS PostgreSQL mediante una variable de entorno. De esta forma, las distintas sucursales trabajan sobre una base centralizada.”

## 7. Repetir la demo

Ejecutar **reset_demo.bat** mientras la aplicación local está encendida para volver a los datos iniciales.
