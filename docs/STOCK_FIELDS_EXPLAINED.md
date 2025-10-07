# 📦 Explicación de Campos de Stock

Este documento explica los diferentes campos de stock en tu base de datos y por qué el sistema de alertas usa `cantidad_disponible`.

## 🗄️ Campos en la tabla `stock_productos`

### 1. **`cantidad`** (Stock Total)
- **Qué es**: Stock físico total en el almacén
- **Incluye**: Todo lo que está en el almacén
- **Ejemplo**: 100 unidades

### 2. **`cantidad_reservada`** (Stock Reservado)
- **Qué es**: Productos apartados para pedidos/ventas pendientes
- **Estado**: Físicamente en el almacén pero comprometidos
- **Ejemplo**: 20 unidades reservadas para pedidos

### 3. **`cantidad_disponible`** (Stock Disponible)
- **Qué es**: Stock realmente disponible para vender
- **Fórmula**: `cantidad - cantidad_reservada`
- **Ejemplo**: 80 unidades disponibles

---

## 🎯 ¿Por qué usar `cantidad_disponible`?

### Escenario Real:

```
Producto: Coca-Cola 2L
Stock mínimo configurado: 50 unidades

Situación:
├─ cantidad (total): 100 unidades
├─ cantidad_reservada: 60 unidades (pedidos pendientes)
└─ cantidad_disponible: 40 unidades (100 - 60)
```

### ❌ Si usamos `cantidad` (total):
```
✗ cantidad (100) > stock_minimo (50)
✗ NO ALERTA
✗ PROBLEMA: Solo tienes 40 disponibles, necesitas 50!
```

### ✅ Si usamos `cantidad_disponible`:
```
✓ cantidad_disponible (40) < stock_minimo (50)
✓ SÍ ALERTA
✓ CORRECTO: Te avisa que necesitas comprar
```

---

## 📊 Ejemplo Completo

### Caso 1: Stock aparentemente suficiente

| Campo | Valor |
|-------|-------|
| `cantidad` | 80 |
| `cantidad_reservada` | 50 |
| `cantidad_disponible` | 30 |
| `stock_minimo` | 50 |

**Análisis**:
- Sin considerar reservas: 80 > 50 → ✗ No alertaría (error)
- Considerando disponible: 30 < 50 → ✅ Alerta correctamente

**Realidad**: Solo tienes 30 unidades libres, necesitas comprar.

---

### Caso 2: Sin reservas

| Campo | Valor |
|-------|-------|
| `cantidad` | 40 |
| `cantidad_reservada` | 0 |
| `cantidad_disponible` | 40 |
| `stock_minimo` | 50 |

**Análisis**:
- Ambos enfoques alertan (40 < 50) → ✅ Correcto

**Conclusión**: Cuando no hay reservas, ambos campos dan el mismo resultado.

---

### Caso 3: Stock crítico con reservas

| Campo | Valor |
|-------|-------|
| `cantidad` | 25 |
| `cantidad_reservada` | 20 |
| `cantidad_disponible` | 5 |
| `stock_minimo` | 50 |

**Email que recibirás**:
```
🔴 PRODUCTO CRÍTICO:

• Coca-Cola 2L
  📦 Stock disponible: 5 unidades (10% del mínimo)
  🔒 Stock reservado: 20 unidades
  📊 Stock total: 25 unidades
  ⚠️ Stock mínimo: 50 unidades
  📉 Déficit: 45 unidades
  🏢 Almacén: Principal
```

**Contexto completo**:
- Tienes 25 unidades físicas
- 20 ya están comprometidas
- Solo 5 libres para vender
- Necesitas 50 → Déficit de 45

---

## 🔄 Actualización de `cantidad_disponible`

Tu sistema Laravel debería actualizar este campo cuando:

### 1. Entra stock nuevo:
```sql
UPDATE stock_productos
SET cantidad = cantidad + 100,
    cantidad_disponible = cantidad_disponible + 100
WHERE producto_id = 1;
```

### 2. Se reserva para un pedido:
```sql
UPDATE stock_productos
SET cantidad_reservada = cantidad_reservada + 10,
    cantidad_disponible = cantidad - (cantidad_reservada + 10)
WHERE producto_id = 1;
```

### 3. Se confirma/cancela una reserva:
```sql
-- Confirmar (sale del almacén)
UPDATE stock_productos
SET cantidad = cantidad - 10,
    cantidad_reservada = cantidad_reservada - 10
WHERE producto_id = 1;

-- Cancelar (libera la reserva)
UPDATE stock_productos
SET cantidad_reservada = cantidad_reservada - 10,
    cantidad_disponible = cantidad_disponible + 10
WHERE producto_id = 1;
```

---

## 🎯 Configuración del Sistema de Alertas

El sistema está configurado para:

### ✅ Considerar:
- `cantidad_disponible` (stock realmente libre)
- `controlar_stock = true` (solo productos que necesitan control)
- `activo = true` (solo productos activos)
- `stock_minimo > 0` (solo productos con mínimo configurado)

### ❌ NO considerar:
- Productos con `controlar_stock = false`
- Productos inactivos
- Productos sin mínimo configurado
- Almacenes inactivos

---

## 💡 Recomendaciones

### 1. Mantén `cantidad_disponible` sincronizado
Usa triggers o lógica en Laravel para mantenerlo actualizado:

```sql
-- Trigger ejemplo (opcional)
CREATE OR REPLACE FUNCTION actualizar_disponible()
RETURNS TRIGGER AS $$
BEGIN
    NEW.cantidad_disponible = NEW.cantidad - NEW.cantidad_reservada;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_disponible
BEFORE INSERT OR UPDATE ON stock_productos
FOR EACH ROW
EXECUTE FUNCTION actualizar_disponible();
```

### 2. Verifica consistencia periódicamente

```sql
-- Query para detectar inconsistencias
SELECT
    p.nombre,
    sp.cantidad,
    sp.cantidad_reservada,
    sp.cantidad_disponible,
    (sp.cantidad - sp.cantidad_reservada) AS deberia_ser
FROM stock_productos sp
JOIN productos p ON sp.producto_id = p.id
WHERE sp.cantidad_disponible != (sp.cantidad - sp.cantidad_reservada);
```

### 3. Configura `stock_minimo` adecuadamente

Considera:
- Demanda promedio diaria/semanal
- Tiempo de reposición del proveedor
- Reservas típicas

**Ejemplo**:
```
Demanda: 20 unidades/día
Tiempo reposición: 3 días
Reservas promedio: 30 unidades

Stock mínimo recomendado:
= (20 unidades/día × 3 días) + 30 reservas + margen seguridad
= 60 + 30 + 20
= 110 unidades
```

---

## 🧪 Pruebas

Para probar el sistema:

```sql
-- 1. Producto con stock bajo disponible
UPDATE stock_productos
SET cantidad = 60,
    cantidad_reservada = 50,
    cantidad_disponible = 10
WHERE producto_id = 1;

-- 2. Ejecutar test
-- python scripts/test_alertas.py

-- 3. Deberías recibir alerta mostrando:
--    - Stock disponible: 10
--    - Stock reservado: 50
--    - Stock total: 60
```

---

## ✅ Resumen

**El sistema de alertas usa `cantidad_disponible` porque**:
1. ✅ Es el stock realmente disponible para vender
2. ✅ Considera reservas/pedidos pendientes
3. ✅ Da alertas más precisas
4. ✅ Evita quedarte sin stock aunque parezca que tienes

**Resultado**: Alertas más inteligentes y útiles para tomar decisiones de compra.
