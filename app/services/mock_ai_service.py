"""
Mock AI Service for fallback when OpenAI is unavailable.
Provides intelligent SQL generation using pattern matching and templates.
"""

import re
import time
from typing import Dict, List, Any, Optional

from app.core.logging import get_logger
from app.database import DatabaseManager

logger = get_logger("mock_ai_service")


class MockAIService:
    """Mock AI service that generates SQL based on pattern matching."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sql_patterns = self._initialize_sql_patterns()
        self.answer_templates = self._initialize_answer_templates()

    def _initialize_sql_patterns(self) -> List[Dict[str, Any]]:
        """Initialize SQL generation patterns."""
        return [
            # Count queries
            {
                "keywords": ["cuántos", "cuántas", "cantidad", "total", "número"],
                "entities": ["productos", "productos"],
                "sql_template": "SELECT COUNT(*) as total FROM productos WHERE activo = true",
                "priority": 10
            },
            {
                "keywords": ["cuántos", "cuántas", "cantidad"],
                "entities": ["almacenes", "almacén"],
                "sql_template": "SELECT COUNT(*) as total FROM almacenes WHERE activo = true",
                "priority": 10
            },
            {
                "keywords": ["cuántos", "cuántas", "cantidad"],
                "entities": ["categorías", "categoria"],
                "sql_template": "SELECT COUNT(*) as total FROM categorias WHERE activo = true",
                "priority": 10
            },
            {
                "keywords": ["cuántos", "cuántas", "cantidad"],
                "entities": ["marcas", "marca"],
                "sql_template": "SELECT COUNT(*) as total FROM marcas WHERE activo = true",
                "priority": 10
            },

            # Stock queries
            {
                "keywords": ["stock", "inventario", "existencias"],
                "entities": ["bajo", "mínimo", "poco"],
                "sql_template": "SELECT p.nombre, sp.cantidad FROM productos p JOIN stock_productos sp ON p.id = sp.producto_id WHERE sp.cantidad <= p.stock_minimo LIMIT 10",
                "priority": 15
            },
            {
                "keywords": ["stock", "inventario"],
                "entities": ["almacén", "almacen"],
                "sql_template": "SELECT p.nombre, sp.cantidad, a.nombre as almacen FROM productos p JOIN stock_productos sp ON p.id = sp.producto_id JOIN almacenes a ON sp.almacen_id = a.id LIMIT 10",
                "priority": 12
            },

            # List queries
            {
                "keywords": ["lista", "muestra", "ver", "mostrar"],
                "entities": ["productos", "producto"],
                "sql_template": "SELECT id, nombre, descripcion FROM productos WHERE activo = true LIMIT 10",
                "priority": 8
            },
            {
                "keywords": ["lista", "muestra", "ver", "mostrar"],
                "entities": ["almacenes", "almacén"],
                "sql_template": "SELECT id, nombre, direccion, responsable FROM almacenes WHERE activo = true LIMIT 10",
                "priority": 8
            },
            {
                "keywords": ["lista", "muestra", "ver", "mostrar"],
                "entities": ["categorías", "categoria"],
                "sql_template": "SELECT id, nombre, descripcion FROM categorias WHERE activo = true LIMIT 10",
                "priority": 8
            },

            # Movements queries
            {
                "keywords": ["movimientos", "movimiento", "últimos", "recientes"],
                "entities": ["inventario", "stock"],
                "sql_template": "SELECT mi.id, mi.cantidad, mi.fecha, mi.tipo, p.nombre as producto FROM movimientos_inventario mi JOIN stock_productos sp ON mi.stock_producto_id = sp.id JOIN productos p ON sp.producto_id = p.id ORDER BY mi.fecha DESC LIMIT 10",
                "priority": 12
            },

            # Transfers queries
            {
                "keywords": ["transferencias", "transferencia", "traslados"],
                "entities": ["inventario", "productos"],
                "sql_template": "SELECT t.numero, t.fecha, ao.nombre as origen, ad.nombre as destino, t.estado FROM transferencia_inventarios t JOIN almacenes ao ON t.almacen_origen_id = ao.id JOIN almacenes ad ON t.almacen_destino_id = ad.id ORDER BY t.fecha DESC LIMIT 10",
                "priority": 12
            },

            # Price queries
            {
                "keywords": ["precio", "precios", "costo", "valor"],
                "entities": ["productos", "promedio", "más caros", "más baratos"],
                "sql_template": "SELECT p.nombre, pp.precio FROM productos p JOIN precios_producto pp ON p.id = pp.producto_id WHERE pp.activo = true ORDER BY pp.precio DESC LIMIT 10",
                "priority": 10
            },

            # Default fallback
            {
                "keywords": ["*"],
                "entities": ["*"],
                "sql_template": "SELECT 'Consulta no reconocida. Intenta preguntar sobre: productos, almacenes, stock, movimientos, transferencias o precios.' as mensaje",
                "priority": 1
            }
        ]

    def _initialize_answer_templates(self) -> Dict[str, str]:
        """Initialize answer templates for different query types."""
        return {
            "count": "Se encontraron {count} {entity} en total.",
            "list": "Aquí tienes la lista de {entity}:",
            "stock_low": "Los siguientes productos tienen stock bajo:",
            "movements": "Los últimos movimientos de inventario son:",
            "transfers": "Las últimas transferencias de inventario son:",
            "prices": "Los precios de productos son:",
            "error": "No se pudo procesar la consulta. {message}",
            "default": "Consulta procesada exitosamente."
        }

    async def generate_sql_query(self, human_query: str) -> str:
        """Generate SQL query using pattern matching."""
        start_time = time.time()

        query_lower = human_query.lower()
        best_match = None
        best_score = 0

        for pattern in self.sql_patterns:
            score = 0

            # Check keyword matches
            keyword_matches = 0
            for keyword in pattern["keywords"]:
                if keyword == "*" or keyword in query_lower:
                    keyword_matches += 1

            # Check entity matches
            entity_matches = 0
            for entity in pattern["entities"]:
                if entity == "*" or entity in query_lower:
                    entity_matches += 1

            # Calculate score
            if keyword_matches > 0 and entity_matches > 0:
                score = (keyword_matches + entity_matches) * pattern["priority"]

                if score > best_score:
                    best_score = score
                    best_match = pattern

        # Use best match or fallback
        if best_match:
            sql_query = best_match["sql_template"]
        else:
            sql_query = "SELECT 'No se pudo generar una consulta SQL para esta pregunta.' as mensaje"

        execution_time = time.time() - start_time
        logger.info(f"Generated SQL using pattern matching in {execution_time:.3f}s: {sql_query[:100]}...")

        return sql_query

    async def build_answer(self, result: List[Dict[str, Any]], human_query: str) -> str:
        """Build natural language answer from SQL results."""
        start_time = time.time()

        if not result:
            return "No se encontraron resultados para tu consulta."

        # Detect query type and format answer accordingly
        query_lower = human_query.lower()

        if any(word in query_lower for word in ["cuántos", "cuántas", "cantidad", "total"]):
            # Count query
            if "total" in result[0]:
                count = result[0]["total"]
                entity = self._extract_entity(query_lower)
                return f"Se encontraron {count} {entity} en total."

        elif any(word in query_lower for word in ["stock", "bajo", "mínimo"]):
            # Stock query
            if len(result) > 1 or "cantidad" in str(result[0]):
                items = []
                for row in result[:5]:  # Limit to 5 items
                    if "nombre" in row and "cantidad" in row:
                        items.append(f"- {row['nombre']}: {row['cantidad']} unidades")
                return "Productos con stock:\n" + "\n".join(items)

        elif any(word in query_lower for word in ["movimientos", "últimos"]):
            # Movements query
            items = []
            for row in result[:5]:
                if "producto" in row and "tipo" in row:
                    items.append(f"- {row['producto']}: {row['tipo']} ({row.get('cantidad', 'N/A')} unidades)")
            return "Últimos movimientos de inventario:\n" + "\n".join(items)

        elif any(word in query_lower for word in ["transferencias", "traslados"]):
            # Transfers query
            items = []
            for row in result[:5]:
                if "numero" in row:
                    items.append(f"- {row['numero']}: {row.get('origen', 'N/A')} → {row.get('destino', 'N/A')} ({row.get('estado', 'N/A')})")
            return "Últimas transferencias:\n" + "\n".join(items)

        elif any(word in query_lower for word in ["precio", "precios"]):
            # Price query
            items = []
            for row in result[:5]:
                if "nombre" in row and "precio" in row:
                    items.append(f"- {row['nombre']}: ${row['precio']}")
            return "Precios de productos:\n" + "\n".join(items)

        elif any(word in query_lower for word in ["lista", "muestra", "ver"]):
            # List query
            items = []
            for row in result[:5]:
                if "nombre" in row:
                    items.append(f"- {row['nombre']}")
            entity = self._extract_entity(query_lower)
            return f"Lista de {entity}:\n" + "\n".join(items)

        # Default formatting
        if len(result) == 1 and len(result[0]) == 1:
            # Single value
            value = list(result[0].values())[0]
            return str(value)
        else:
            # Multiple results
            return f"Se encontraron {len(result)} resultados para tu consulta."

    def _extract_entity(self, query: str) -> str:
        """Extract entity name from query."""
        entities = {
            "productos": "productos",
            "producto": "productos",
            "almacenes": "almacenes",
            "almacén": "almacenes",
            "categorías": "categorías",
            "categoria": "categorías",
            "marcas": "marcas",
            "marca": "marcas"
        }

        for entity, canonical in entities.items():
            if entity in query:
                return canonical

        return "elementos"

    def get_available_tables(self) -> List[str]:
        """Get list of available tables."""
        try:
            return self.db_manager.get_available_tables()
        except Exception as e:
            logger.error(f"Error getting available tables: {e}")
            return []

    def get_table_schema(self, table_names: Optional[List[str]] = None) -> str:
        """Get schema information for specified tables."""
        try:
            return self.db_manager.get_table_info(table_names)
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return "Schema information not available"