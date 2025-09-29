import time
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date

from app.core.exceptions import DatabaseException, ValidationException
from app.core.logging import get_logger
from app.database import DatabaseManager
from app.services.ai_service import AIService
from app.models.requests import HumanQueryRequest
from app.models.responses import QueryResponse, StructuredTableData, TableColumn

logger = get_logger("query_service")


class QueryService:
    """Servicio para manejar el flujo completo de procesamiento de consultas."""

    def __init__(self, db_manager: DatabaseManager, ai_service: AIService):
        self.db_manager = db_manager
        self.ai_service = ai_service

    async def process_human_query(self, request: HumanQueryRequest) -> QueryResponse:
        """Procesa una consulta humana completa desde la solicitud hasta la respuesta."""
        start_time = time.time()

        try:
            logger.info(f"Processing query: {request.human_query[:100]}...")

            # Paso 1: Generar SQL a partir de lenguaje natural
            sql_query = await self.ai_service.generate_sql_query(request.human_query)
            logger.info(f"Generated SQL: {sql_query}")

            # Paso 2: Aplicar límite si se solicita (solo para SELECT)
            if request.limit_results and sql_query.upper().strip().startswith('SELECT'):
                sql_query = self._apply_limit_to_query(sql_query, request.limit_results)

            # Paso 3: Determinar el tipo de operación y ejecutar
            sql_upper = sql_query.upper().strip()
            raw_data = []
            rows_affected = 0

            if sql_upper.startswith('SELECT'):
                # Consulta de lectura
                raw_data = self.db_manager.execute_query(sql_query)
                logger.info(f"Query returned {len(raw_data)} rows")
            else:
                # Operación de escritura (INSERT, UPDATE, DELETE)
                rows_affected = self.db_manager.execute_non_query(sql_query)
                logger.info(f"Query affected {rows_affected} rows")

                # Para operaciones de escritura, crear un resultado informativo
                operation_type = sql_upper.split()[0]  # INSERT, UPDATE, or DELETE
                raw_data = []

            # Paso 4: Generar respuesta en lenguaje natural
            if sql_upper.startswith('SELECT'):
                answer = await self.ai_service.build_answer(raw_data, request.human_query)
            else:
                # Para operaciones de escritura, generar respuesta basada en filas afectadas
                answer = await self._build_write_operation_answer(
                    sql_upper.split()[0],
                    rows_affected,
                    request.human_query
                )

            # Paso 5: Convertir a datos de tabla estructurada para sistemas externos (solo SELECT)
            structured_data = None
            if raw_data:
                structured_data = self._convert_to_structured_data(raw_data)

            # Paso 6: Preparar información adicional si se solicita
            table_info = None
            if request.include_table_info:
                table_info = self.ai_service.get_table_schema()

            execution_time = time.time() - start_time

            response = QueryResponse(
                answer=answer,
                sql_query=sql_query,
                raw_data=raw_data if len(raw_data) <= 50 else raw_data[:50],  # Limit raw data
                structured_data=structured_data,
                execution_time=execution_time,
                table_info=table_info
            )

            logger.info(f"Query processed successfully in {execution_time:.3f}s")
            return response

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error processing query after {execution_time:.3f}s: {e}")
            raise

    async def _build_write_operation_answer(
        self,
        operation_type: str,
        rows_affected: int,
        human_query: str
    ) -> str:
        """Construye una respuesta en lenguaje natural para operaciones de escritura."""
        try:
            # Usar el AI service para generar una respuesta natural
            result_info = {
                "operation": operation_type,
                "rows_affected": rows_affected,
                "success": rows_affected > 0
            }

            answer = await self.ai_service.build_answer([result_info], human_query)
            return answer
        except Exception as e:
            logger.warning(f"Error building write operation answer with AI: {e}")
            # Fallback a respuesta simple
            if rows_affected == 0:
                return f"No se realizaron cambios en la base de datos."
            elif rows_affected == 1:
                return f"Operación completada exitosamente. Se afectó 1 registro."
            else:
                return f"Operación completada exitosamente. Se afectaron {rows_affected} registros."

    def _apply_limit_to_query(self, sql_query: str, limit: int) -> str:
        """Apply LIMIT clause to SQL query if not already present."""
        sql_upper = sql_query.upper().strip()

        # Check if LIMIT is already present
        if 'LIMIT' in sql_upper:
            return sql_query

        # Add LIMIT clause
        if sql_query.rstrip().endswith(';'):
            sql_query = sql_query.rstrip()[:-1]  # Remove semicolon

        return f"{sql_query} LIMIT {limit}"

    def _convert_to_structured_data(self, raw_data: List[Dict[str, Any]]) -> Optional[StructuredTableData]:
        """Convert raw database results to structured table data for external systems."""
        if not raw_data:
            return None

        try:
            # Extract column information from the first row
            first_row = raw_data[0]
            columns = []

            for column_name, value in first_row.items():
                # Determine data type based on the value
                data_type = self._determine_data_type(value)
                nullable = value is None  # Basic nullability check

                columns.append(TableColumn(
                    name=column_name,
                    type=data_type,
                    nullable=nullable
                ))

            # Convert data rows to arrays
            rows = []
            for row_dict in raw_data:
                row_array = []
                for column in columns:
                    value = row_dict.get(column.name)
                    # Convert special types to JSON-serializable values
                    row_array.append(self._convert_value_for_json(value))
                rows.append(row_array)

            return StructuredTableData(
                columns=columns,
                rows=rows,
                total_rows=len(raw_data)
            )

        except Exception as e:
            logger.warning(f"Error converting to structured data: {e}")
            return None

    def _determine_data_type(self, value: Any) -> str:
        """Determine the data type for a column based on its value."""
        if value is None:
            return "string"  # Default to string for null values

        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float, Decimal)):
            return "number"
        elif isinstance(value, (datetime, date)):
            return "date"
        else:
            return "string"

    def _convert_value_for_json(self, value: Any) -> Any:
        """Convert database values to JSON-serializable formats."""
        if value is None:
            return None
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        else:
            return value

    async def get_database_schema(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            available_tables = self.ai_service.get_available_tables()
            table_info = self.ai_service.get_table_schema(table_names)

            return {
                "available_tables": available_tables,
                "schema_info": table_info,
                "filtered_tables": table_names if table_names else available_tables
            }
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            raise DatabaseException(f"Error getting database schema: {e}")

    async def validate_query_safety(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """Validate that the SQL query is safe to execute."""
        try:
            sql_upper = sql_query.upper().strip()

            # Check for dangerous keywords
            dangerous_keywords = [
                'DROP', 'TRUNCATE', 'ALTER TABLE', 'DROP TABLE', 'GRANT', 'REVOKE', 'EXEC'
            ]

            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    return False, f"Query contains dangerous keyword: {keyword}"

            # Ensure it's a valid SQL statement
            allowed_statements = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
            if not any(sql_upper.startswith(stmt) for stmt in allowed_statements):
                return False, "Only SELECT, INSERT, UPDATE, and DELETE statements are allowed"

            # Check for multiple statements (basic check)
            if ';' in sql_query[:-1]:  # Allow semicolon at the end
                return False, "Multiple statements are not allowed"

            return True, None

        except Exception as e:
            logger.error(f"Error validating query safety: {e}")
            return False, f"Error validating query: {e}"

    def get_query_statistics(self) -> Dict[str, Any]:
        """Get statistics about query processing."""
        # This could be extended to track actual statistics
        return {
            "available_tables": len(self.ai_service.get_available_tables()),
            "service_status": "operational",
            "supported_operations": ["SELECT, INSERT, UPDATE, DELETE queries", "Natural language processing"]
        }