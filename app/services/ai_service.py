import time
from typing import Dict, List, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from app.core.exceptions import LLMException, SQLGenerationException
from app.core.logging import get_logger
from app.database import DatabaseManager
from app.services.mock_ai_service import MockAIService

logger = get_logger("ai_service")


class AIService:
    """Service for AI-powered SQL generation and natural language processing."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._llm = None
        self._query_chain = None
        self._answer_chain = None
        self._claude_available = False
        self._mock_service = None
        self._initialize_llm()
        self._initialize_chains()

        # Initialize fallback service if needed
        if not self._claude_available and settings.claude_fallback_enabled:
            self._mock_service = MockAIService(db_manager)
            logger.info("Initialized Mock AI Service as fallback")

    def _initialize_llm(self):
        """Initialize the Language Model."""
        if settings.claude_demo_mode:
            logger.info("Claude Demo Mode enabled - using fallback service")
            self._claude_available = False
            return

        try:
            self._llm = ChatAnthropic(
                model=settings.claude_model,
                api_key=settings.claude_api_key,
                temperature=0,  # For consistent SQL generation
                max_tokens=2000,
                timeout=30
            )
            logger.info(f"Initialized LLM with model: {settings.claude_model}")
            self._claude_available = True
        except Exception as e:
            logger.warning(f"Failed to initialize Claude LLM: {e}")
            if settings.claude_fallback_enabled:
                logger.info("Will use fallback AI service instead")
                self._claude_available = False
            else:
                raise LLMException(f"Failed to initialize LLM: {e}")

    def _initialize_chains(self):
        """Initialize Langchain chains for SQL generation and answer formatting."""
        if not self._claude_available:
            logger.info("Skipping chain initialization - Claude not available")
            return

        try:
            # SQL generation chain
            self._query_chain = create_sql_query_chain(
                self._llm,
                self.db_manager.langchain_db
            )

            # Answer formatting chain
            answer_prompt = ChatPromptTemplate.from_template(
                """Basándote en la pregunta del usuario y los resultados de la base de datos,
                proporciona una respuesta clara y concisa en español.

                Pregunta del usuario: {human_query}

                Resultados de la base de datos: {result}

                Instrucciones:
                - Responde en español de manera natural y conversacional
                - Si no hay resultados, indica que no se encontraron datos
                - Si hay muchos resultados, proporciona un resumen útil
                - Incluye números específicos cuando sea relevante
                - Si los datos parecen incompletos o hay un error, indícalo claramente

                Respuesta:"""
            )

            self._answer_chain = answer_prompt | self._llm
            logger.info("Initialized Langchain chains successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chains: {e}")
            if not settings.claude_fallback_enabled:
                raise LLMException(f"Failed to initialize chains: {e}")

    async def generate_sql_query(self, human_query: str) -> str:
        """Generate SQL query from natural language."""
        # Use fallback service if Claude is not available
        if not self._claude_available and self._mock_service:
            logger.info("Using fallback AI service for SQL generation")
            return await self._mock_service.generate_sql_query(human_query)

        if not self._claude_available:
            raise SQLGenerationException("Claude not available and fallback disabled")

        try:
            start_time = time.time()

            # Enhanced prompt for better SQL generation
            enhanced_query = f"""
            Genera una consulta SQL segura y eficiente para la siguiente pregunta en español.
            La base de datos contiene información de inventario y productos.

            Pregunta: {human_query}

            Consideraciones importantes:
            - Solo usa SELECT statements
            - No uses funciones o sintaxis específica de PostgreSQL a menos que sea necesario
            - Incluye JOIN apropiados cuando sea necesario
            - Usa aliases para claridad
            - Limita resultados si es apropiado (LIMIT)
            """

            response = await self._query_chain.ainvoke({"question": enhanced_query})

            # Clean the response
            sql_query = self._clean_sql_response(response)

            execution_time = time.time() - start_time
            logger.info(f"Generated SQL query in {execution_time:.3f}s: {sql_query[:100]}...")

            return sql_query

        except Exception as e:
            logger.error(f"Error generating SQL query with Claude: {e}")

            # Try fallback if available
            if self._mock_service and settings.claude_fallback_enabled:
                logger.info("Falling back to mock AI service")
                return await self._mock_service.generate_sql_query(human_query)

            raise SQLGenerationException(f"Error generating SQL query: {e}")

    def _clean_sql_response(self, response: str) -> str:
        """Clean and validate the SQL response from LLM."""
        if hasattr(response, 'content'):
            sql_query = response.content
        else:
            sql_query = str(response)

        # Extract SQL from Claude's verbose response
        # Look for SQL after common markers
        sql_markers = [
            "SQLQuery:",
            "SQL:",
            "Query:",
            "```sql",
            "```",
            "SELECT"  # Direct SQL start
        ]

        # Try to find SQL in the response
        lines = sql_query.split('\n')
        sql_lines = []
        found_sql = False

        for line in lines:
            original_line = line
            line = line.strip()

            # Skip empty lines
            if not line:
                if found_sql:
                    # If we're in SQL and hit empty line, continue collecting
                    continue
                else:
                    continue

            # Check if this line contains SQL markers
            if any(marker.upper() in line.upper() for marker in sql_markers[:5]):  # Don't include "SELECT" here
                found_sql = True
                # If the line contains SQLQuery: or similar, extract what comes after
                for marker in sql_markers[:5]:
                    if marker.upper() in line.upper():
                        # Find the marker and take everything after it
                        marker_pos = line.upper().find(marker.upper())
                        if marker_pos >= 0:
                            line = line[marker_pos + len(marker):].strip()
                            break

                if line:  # Only add if there's content after removing marker
                    sql_lines.append(line)
            elif found_sql and line.upper().startswith('SELECT'):
                # We found a SELECT statement
                sql_lines.append(line)
            elif found_sql:
                # We're in SQL block, add the line (could be continuation)
                sql_lines.append(line)
            elif line.upper().startswith('SELECT'):
                # Direct SQL start
                found_sql = True
                sql_lines.append(line)

        # Join the SQL lines
        if sql_lines:
            sql_query = ' '.join(sql_lines)

        # Additional cleanup
        sql_query = sql_query.strip()

        # Remove trailing punctuation that might interfere
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3].strip()
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1].strip()

        # Basic validation
        if not sql_query:
            raise SQLGenerationException("Generated SQL query is empty")

        # Security check - ensure it's a SELECT statement
        if not sql_query.upper().startswith('SELECT'):
            raise SQLGenerationException("Generated query is not a SELECT statement")

        return sql_query

    async def build_answer(
        self,
        result: List[Dict[str, Any]],
        human_query: str
    ) -> str:
        """Build natural language answer from SQL results."""
        # Use fallback service if Claude is not available
        if not self._claude_available and self._mock_service:
            logger.info("Using fallback AI service for answer building")
            return await self._mock_service.build_answer(result, human_query)

        if not self._claude_available:
            # Basic fallback formatting if no mock service
            if not result:
                return "No se encontraron resultados para tu consulta."
            elif len(result) == 1 and len(result[0]) == 1:
                value = list(result[0].values())[0]
                return f"Resultado: {value}"
            else:
                return f"Se encontraron {len(result)} resultados para tu consulta."

        try:
            start_time = time.time()

            # Format results for better LLM processing
            if not result:
                formatted_result = "No se encontraron resultados."
            elif len(result) == 1 and len(result[0]) == 1:
                # Single value result
                value = list(result[0].values())[0]
                formatted_result = f"Valor: {value}"
            else:
                # Multiple results - limit for LLM context
                limited_result = result[:20]  # Limit to first 20 results
                formatted_result = str(limited_result)
                if len(result) > 20:
                    formatted_result += f"\n... y {len(result) - 20} resultados más"

            response = await self._answer_chain.ainvoke({
                "human_query": human_query,
                "result": formatted_result
            })

            execution_time = time.time() - start_time
            logger.info(f"Built natural language answer in {execution_time:.3f}s")

            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            logger.error(f"Error building answer with Claude: {e}")

            # Try fallback if available
            if self._mock_service and settings.claude_fallback_enabled:
                logger.info("Falling back to mock AI service for answer")
                return await self._mock_service.build_answer(result, human_query)

            raise LLMException(f"Error building answer: {e}")

    def get_available_tables(self) -> List[str]:
        """Get list of available tables in the database."""
        try:
            return self.db_manager.langchain_db.get_usable_table_names()
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