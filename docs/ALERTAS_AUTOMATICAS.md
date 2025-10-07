# 📧 Sistema de Alertas Automáticas

Sistema de monitoreo automático de inventario con alertas por email implementado en el Agente Inteligente.

## 🎯 ¿Qué hace?

El agente revisa automáticamente el inventario cada 30 minutos y envía alertas por email cuando detecta productos con stock bajo el mínimo.

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Crear tabla en PostgreSQL

Ejecuta el script SQL para crear la tabla de control de alertas:

```bash
psql -h tu_host -U tu_usuario -d tu_base_de_datos -f scripts/create_alertas_table.sql
```

O ejecuta manualmente:

```sql
-- Ver contenido de scripts/create_alertas_table.sql
```

### 3. Configurar variables de entorno

Edita el archivo `.env` y configura:

```bash
# ===== ALERTAS AUTOMÁTICAS =====

# Intervalo de verificación (en minutos)
ALERT_CHECK_INTERVAL=30
ALERT_RUN_ON_STARTUP=false

# SMTP Configuration (Brevo)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=989e8b001@smtp-brevo.com
SMTP_PASSWORD=LETgcRDSzN9xItCm
ALERT_EMAIL_FROM=989e8b001@smtp-brevo.com
ALERT_EMAIL_TO_STR=destinatario1@ejemplo.com,destinatario2@ejemplo.com

# Spam Control
ALERT_SPAM_INTERVAL_HOURS=2
```

**IMPORTANTE**: Cambia `ALERT_EMAIL_TO_STR` por los emails reales donde quieres recibir las alertas.

### 4. Iniciar el agente

```bash
python main.py
```

El scheduler se iniciará automáticamente junto con la API.

## 📊 Cómo funciona

### Flujo automático cada 30 minutos:

```
┌─────────────────────────────────────┐
│  Scheduler despierta                │
│         ↓                           │
│  Alert Detector consulta BD         │
│    - SQL: detecta stock bajo        │
│    - Clasifica por severidad        │
│         ↓                           │
│  Alert Intelligence filtra          │
│    - Spam control                   │
│    - Agrupamiento                   │
│         ↓                           │
│  Notification Manager envía         │
│    - Formatea email HTML            │
│    - Envía via Brevo SMTP           │
│    - Registra en BD                 │
│         ↓                           │
│  Scheduler duerme hasta próximo     │
└─────────────────────────────────────┘
```

### Clasificación de severidad:

- 🔴 **CRÍTICO**: Stock disponible < 20% del mínimo
- 🟠 **MEDIO**: Stock disponible < 50% del mínimo
- 🟡 **BAJO**: Stock disponible < 100% del mínimo

**Nota**: El sistema usa `cantidad_disponible` (no cantidad total), lo que significa que excluye el stock reservado para pedidos/ventas.

### Spam Control:

- No envía alertas duplicadas del mismo producto en 2 horas
- EXCEPTO si la severidad aumentó (MEDIO → CRÍTICO)
- Todas las alertas se agrupan en 1 solo email

## 📧 Formato del Email

Los emails incluyen:

- **Asunto**: Indica severidad y cantidad de productos
- **Cuerpo HTML**: Información detallada de cada producto
  - Nombre del producto
  - Stock disponible vs mínimo
  - Stock reservado (si aplica)
  - Stock total (si hay reservas)
  - Porcentaje de stock
  - Déficit
  - Almacén
- **Agrupamiento**: Por severidad (críticos, medios, bajos)

**Ejemplo de email**:
```
• Coca-Cola 2L
  📦 Stock disponible: 15 unidades (30% del mínimo)
  🔒 Stock reservado: 10 unidades
  📊 Stock total: 25 unidades
  ⚠️ Stock mínimo: 50 unidades
  📉 Déficit: 35 unidades
  🏢 Almacén: Principal
```

## ⚙️ Configuración

### Cambiar intervalo de verificación:

En `.env`:
```bash
ALERT_CHECK_INTERVAL=15  # Cada 15 minutos
```

### Cambiar spam control:

En `.env`:
```bash
ALERT_SPAM_INTERVAL_HOURS=1  # 1 hora entre alertas
```

### Ejecutar verificación al iniciar:

En `.env`:
```bash
ALERT_RUN_ON_STARTUP=true  # Ejecuta inmediatamente al arrancar
```

### Agregar más destinatarios:

En `.env`:
```bash
ALERT_EMAIL_TO_STR=email1@ejemplo.com,email2@ejemplo.com,email3@ejemplo.com
```

## 🧪 Pruebas

### Probar manualmente:

Crea un script de prueba:

```python
# test_alertas.py
from app.services.alert_detector import alert_detector
from app.services.notification_manager import notification_manager

# 1. Detectar stock bajo
alertas = alert_detector.detectar_stock_bajo()

print(f"Alertas detectadas: {alertas.total_alertas}")
print(f"  - Críticas: {len(alertas.criticas)}")
print(f"  - Medias: {len(alertas.medias)}")
print(f"  - Bajas: {len(alertas.bajas)}")

# 2. Enviar si hay alertas
if alertas.tiene_alertas:
    exito = notification_manager.enviar_alertas(alertas)
    print(f"Email enviado: {exito}")
```

Ejecuta:
```bash
python test_alertas.py
```

### Simular stock bajo:

```sql
-- Baja temporalmente el stock de un producto para pruebas
UPDATE stock_productos
SET cantidad = 5
WHERE producto_id = 1 AND almacen_id = 1;

-- Espera a que el scheduler ejecute (o ejecuta test_alertas.py)

-- Restaura el stock
UPDATE stock_productos
SET cantidad = 100
WHERE producto_id = 1 AND almacen_id = 1;
```

## 📋 Logs

Los logs del scheduler se encuentran en:

```
logs/app.log
```

Busca líneas como:

```
INFO - Iniciando verificación automática de stock
INFO - Detectados 3 productos con stock bajo
INFO - Email enviado correctamente a: destinatario@ejemplo.com
INFO - Registradas 3 alertas en la base de datos
```

## 🛠️ Troubleshooting

### El scheduler no inicia:

1. Verifica que APScheduler esté instalado:
   ```bash
   pip install apscheduler==3.10.4
   ```

2. Revisa los logs en `logs/app.log`

### No recibo emails:

1. Verifica credenciales SMTP en `.env`
2. Confirma que `ALERT_EMAIL_TO_STR` tenga tu email
3. Revisa spam en tu correo
4. Verifica logs para errores SMTP

### Recibo emails duplicados:

1. Verifica que la tabla `alertas_enviadas` existe
2. Aumenta `ALERT_SPAM_INTERVAL_HOURS`
3. Revisa logs de spam control

### No detecta productos con stock bajo:

1. Verifica que existen productos con:
   - `cantidad_disponible < stock_minimo`
   - `activo = true`
   - `controlar_stock = true`
   - `stock_minimo > 0`

2. Ejecuta manualmente el SQL para verificar:
   ```sql
   SELECT
       p.nombre,
       a.nombre as almacen,
       sp.cantidad_disponible,
       sp.cantidad_reservada,
       sp.cantidad as total,
       p.stock_minimo,
       p.controlar_stock,
       p.activo
   FROM stock_productos sp
   JOIN productos p ON sp.producto_id = p.id
   JOIN almacenes a ON sp.almacen_id = a.id
   WHERE sp.cantidad_disponible < p.stock_minimo
     AND p.activo = true
     AND a.activo = true
     AND p.controlar_stock = true
     AND p.stock_minimo > 0;
   ```

3. Si no hay resultados, simula stock bajo temporalmente:
   ```sql
   -- Ver un producto de prueba
   SELECT id, nombre, stock_minimo FROM productos LIMIT 1;

   -- Bajar temporalmente el stock disponible
   UPDATE stock_productos
   SET cantidad_disponible = 5
   WHERE producto_id = 1 AND almacen_id = 1;

   -- Ejecutar test
   python scripts/test_alertas.py

   -- Restaurar
   UPDATE stock_productos
   SET cantidad_disponible = cantidad - cantidad_reservada
   WHERE producto_id = 1 AND almacen_id = 1;
   ```

## 🔐 Seguridad

- Las credenciales SMTP están en `.env` (no subir a git)
- La tabla `alertas_enviadas` registra todas las alertas (auditoría)
- Los destinatarios se configuran en variables de entorno

## 📊 Monitoreo

### Ver estado del scheduler:

El scheduler imprime logs al iniciar:

```
🚀 SCHEDULER DE ALERTAS INICIADO
Intervalo de verificación: cada 30 minutos
```

### Ver historial de alertas:

```sql
SELECT
    p.nombre AS producto,
    a.nombre AS almacen,
    ae.severidad,
    ae.fecha_envio
FROM alertas_enviadas ae
JOIN productos p ON ae.producto_id = p.id
JOIN almacenes a ON ae.almacen_id = a.id
ORDER BY ae.fecha_envio DESC
LIMIT 20;
```

## 🚀 Despliegue en Railway

Las mismas variables de entorno deben configurarse en Railway:

1. Ve a tu proyecto en Railway
2. Settings → Variables
3. Agrega todas las variables `ALERT_*` y `SMTP_*`

El scheduler se iniciará automáticamente al desplegar.

## 📝 Notas

- El scheduler usa `BackgroundScheduler` (no bloquea FastAPI)
- Solo se ejecuta una instancia del job a la vez (`max_instances=1`)
- Si el agente se reinicia, el scheduler se reinicia automáticamente
- Las alertas se envían en formato HTML + texto plano (compatible con todos los clientes)
