"""
Alert Detector - Detecta productos con stock bajo y clasifica por severidad
"""
from typing import List, Dict
from datetime import datetime, timedelta
from app.database import db_manager
from app.models.alert import ProductoAlerta, AlertaAgrupada, AlertaSeveridad
from app.core.logging import get_logger

logger = get_logger("alert_detector")


class AlertDetector:
    """Detector de alertas de stock bajo"""

    def __init__(self):
        self.db = db_manager

    def detectar_stock_bajo(self, limite: int = 50) -> AlertaAgrupada:
        """
        Detecta productos con stock bajo el mínimo y los clasifica por severidad

        Args:
            limite: Número máximo de productos a procesar por ciclo

        Returns:
            AlertaAgrupada con productos clasificados por severidad
        """
        logger.info("Iniciando detección de stock bajo...")

        try:
            # Ejecutar query para detectar stock bajo
            productos_alerta = self._consultar_stock_bajo(limite)

            if not productos_alerta:
                logger.info("No se detectaron productos con stock bajo")
                return AlertaAgrupada()

            logger.info(f"Detectados {len(productos_alerta)} productos con stock bajo")

            # Clasificar por severidad
            alerta_agrupada = self._clasificar_por_severidad(productos_alerta)

            # Filtrar productos ya alertados recientemente
            alerta_agrupada = self._filtrar_spam(alerta_agrupada)

            logger.info(
                f"Alertas después de filtrar spam: "
                f"{len(alerta_agrupada.criticas)} críticas, "
                f"{len(alerta_agrupada.medias)} medias, "
                f"{len(alerta_agrupada.bajas)} bajas"
            )

            return alerta_agrupada

        except Exception as e:
            logger.error(f"Error al detectar stock bajo: {e}")
            raise

    def _consultar_stock_bajo(self, limite: int) -> List[Dict]:
        """
        Consulta productos con stock bajo el mínimo

        Args:
            limite: Número máximo de resultados

        Returns:
            Lista de diccionarios con información de productos
        """
        query = """
        SELECT
            p.id AS producto_id,
            p.nombre AS producto_nombre,
            p.codigo_barras AS producto_codigo,
            a.id AS almacen_id,
            a.nombre AS almacen_nombre,
            sp.cantidad_disponible AS stock_actual,
            sp.cantidad AS stock_total,
            sp.cantidad_reservada AS stock_reservado,
            p.stock_minimo,
            (p.stock_minimo - sp.cantidad_disponible) AS deficit,
            ROUND((sp.cantidad_disponible::numeric / NULLIF(p.stock_minimo, 0)) * 100, 2) AS porcentaje_stock
        FROM stock_productos sp
        JOIN productos p ON sp.producto_id = p.id
        JOIN almacenes a ON sp.almacen_id = a.id
        WHERE sp.cantidad_disponible < p.stock_minimo
            AND p.activo = true
            AND a.activo = true
            AND p.controlar_stock = true
            AND p.stock_minimo > 0
        ORDER BY porcentaje_stock ASC, deficit DESC
        LIMIT %s
        """

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (limite,))
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()

                    productos = []
                    for row in results:
                        producto = dict(zip(columns, row))
                        productos.append(producto)

                    return productos

        except Exception as e:
            logger.error(f"Error al consultar stock bajo: {e}")
            raise

    def _clasificar_por_severidad(self, productos: List[Dict]) -> AlertaAgrupada:
        """
        Clasifica productos por severidad según porcentaje de stock

        Severidad:
        - CRÍTICO: stock < 20% del mínimo
        - MEDIO: stock < 50% del mínimo
        - BAJO: stock < 100% del mínimo

        Args:
            productos: Lista de productos con stock bajo

        Returns:
            AlertaAgrupada con productos clasificados
        """
        alerta_agrupada = AlertaAgrupada()
        for producto_data in productos:
            porcentaje = producto_data.get('porcentaje_stock', 0)

            # Determinar severidad
            if porcentaje < 20:
                severidad = AlertaSeveridad.CRITICO
            elif porcentaje < 50:
                severidad = AlertaSeveridad.MEDIO
            else:
                severidad = AlertaSeveridad.BAJO
            # Crear modelo de producto alerta
            producto_alerta = ProductoAlerta(
                producto_id=producto_data['producto_id'],
                producto_nombre=producto_data['producto_nombre'],
                producto_codigo=producto_data.get('producto_codigo'),
                almacen_id=producto_data['almacen_id'],
                almacen_nombre=producto_data['almacen_nombre'],
                stock_actual=producto_data['stock_actual'],
                stock_total=producto_data.get('stock_total'),
                stock_reservado=producto_data.get('stock_reservado'),
                stock_minimo=producto_data['stock_minimo'],
                deficit=producto_data['deficit'],
                porcentaje_stock=porcentaje,
                severidad=severidad
            )
            # Agregar a la lista correspondiente
            if severidad == AlertaSeveridad.CRITICO:
                alerta_agrupada.criticas.append(producto_alerta)
            elif severidad == AlertaSeveridad.MEDIO:
                alerta_agrupada.medias.append(producto_alerta)
            else:
                alerta_agrupada.bajas.append(producto_alerta)
        return alerta_agrupada

    def _filtrar_spam(self, alerta_agrupada: AlertaAgrupada, horas: int = 2) -> AlertaAgrupada:
        """
        Filtra productos que ya fueron alertados recientemente (spam control)

        Args:
            alerta_agrupada: Alertas agrupadas
            horas: Horas mínimas entre alertas del mismo producto

        Returns:
            AlertaAgrupada filtrada
        """
        try:
            # Obtener alertas recientes (últimas N horas)
            query = """
            SELECT DISTINCT producto_id, almacen_id, severidad
            FROM alertas_enviadas
            WHERE fecha_envio > %s
            """

            limite_tiempo = datetime.now() - timedelta(hours=horas)

            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (limite_tiempo,))
                    alertas_recientes = cursor.fetchall()

            # Crear set de (producto_id, almacen_id) ya alertados
            alertados = {(row[0], row[1]) for row in alertas_recientes}

            # Crear dict de severidades previas
            severidades_previas = {
                (row[0], row[1]): row[2] for row in alertas_recientes
            }

            # Filtrar cada lista
            alerta_filtrada = AlertaAgrupada()

            def debe_alertar(producto: ProductoAlerta) -> bool:
                """Determina si debe enviar alerta"""
                key = (producto.producto_id, producto.almacen_id)

                # Si no fue alertado antes, sí enviar
                if key not in alertados:
                    return True

                # Si fue alertado pero aumentó la severidad, sí enviar
                severidad_previa = severidades_previas.get(key)
                if severidad_previa == AlertaSeveridad.MEDIO and producto.es_critico:
                    logger.info(
                        f"Producto {producto.producto_nombre} aumentó severidad "
                        f"de {severidad_previa} a {producto.severidad}"
                    )
                    return True
                elif severidad_previa == AlertaSeveridad.BAJO and (producto.es_critico or producto.es_medio):
                    logger.info(
                        f"Producto {producto.producto_nombre} aumentó severidad "
                        f"de {severidad_previa} a {producto.severidad}"
                    )
                    return True

                # Ya fue alertado recientemente y no aumentó severidad
                logger.debug(
                    f"Producto {producto.producto_nombre} ya fue alertado hace menos de {horas} horas"
                )
                return False

            # Filtrar cada lista
            alerta_filtrada.criticas = [p for p in alerta_agrupada.criticas if debe_alertar(p)]
            alerta_filtrada.medias = [p for p in alerta_agrupada.medias if debe_alertar(p)]
            alerta_filtrada.bajas = [p for p in alerta_agrupada.bajas if debe_alertar(p)]

            return alerta_filtrada

        except Exception as e:
            logger.error(f"Error al filtrar spam: {e}")
            # En caso de error, devolver todas las alertas (mejor alertar de más que de menos)
            return alerta_agrupada


# Instancia global
alert_detector = AlertDetector()
