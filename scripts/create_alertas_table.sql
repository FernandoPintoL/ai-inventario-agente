-- Tabla para control de alertas enviadas (spam control y auditoría)
CREATE TABLE IF NOT EXISTS alertas_enviadas (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL,
    almacen_id INTEGER NOT NULL,
    severidad VARCHAR(20) NOT NULL,
    mensaje TEXT,
    destinatarios JSONB,
    fecha_envio TIMESTAMP DEFAULT NOW(),

    -- Índice para búsqueda rápida de alertas recientes
    CONSTRAINT idx_alertas_recientes_unique UNIQUE (producto_id, almacen_id, fecha_envio)
);

-- Índice para verificar alertas recientes eficientemente
CREATE INDEX IF NOT EXISTS idx_alertas_producto_almacen
ON alertas_enviadas(producto_id, almacen_id, fecha_envio DESC);

-- Índice para búsquedas por severidad
CREATE INDEX IF NOT EXISTS idx_alertas_severidad
ON alertas_enviadas(severidad, fecha_envio DESC);

COMMENT ON TABLE alertas_enviadas IS 'Registro de alertas enviadas para control de spam y auditoría';
COMMENT ON COLUMN alertas_enviadas.severidad IS 'CRITICO, MEDIO, BAJO';
COMMENT ON COLUMN alertas_enviadas.destinatarios IS 'Array JSON con emails de destinatarios';
