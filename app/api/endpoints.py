from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List, Optional

from app.models.requests import HumanQueryRequest
from app.models.responses import QueryResponse, ErrorResponse
from app.services import AIService, QueryService
from app.database import db_manager
from app.core.exceptions import (
    DatabaseException,
    SQLGenerationException,
    LLMException,
    ValidationException
)
from app.core.logging import get_logger

logger = get_logger("api")

router = APIRouter(prefix="/api/v1", tags=["intelligent_agent"])

# Dependency injection
def get_ai_service() -> AIService:
    return AIService(db_manager)

def get_query_service(ai_service: AIService = Depends(get_ai_service)) -> QueryService:
    return QueryService(db_manager, ai_service)


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar consulta en lenguaje natural",
    description="Convierte una consulta en lenguaje natural a SQL, la ejecuta y devuelve una respuesta en lenguaje natural"
)
async def process_query(
    request: HumanQueryRequest,
    query_service: QueryService = Depends(get_query_service)
) -> QueryResponse:
    """Procesa una consulta en lenguaje natural y devuelve los resultados."""
    try:
        logger.info(f"Received query request: {request.human_query[:100]}...")
        response = await query_service.process_human_query(request)
        logger.info("Query processed successfully")
        return response

    except ValidationException as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_type": "ValidationException",
                "details": e.details
            }
        )

    except SQLGenerationException as e:
        logger.error(f"SQL generation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "No se pudo generar una consulta SQL válida para tu pregunta. Por favor, reformula la pregunta.",
                "error_type": "SQLGenerationException",
                "details": e.details
            }
        )

    except DatabaseException as e:
        logger.error(f"Database error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Error de conexión con la base de datos. Intenta nuevamente en unos momentos.",
                "error_type": "DatabaseException",
                "details": e.details
            }
        )

    except LLMException as e:
        logger.error(f"LLM error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "Error en el servicio de inteligencia artificial. Intenta nuevamente.",
                "error_type": "LLMException",
                "details": e.details
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error interno del servidor. Contacta al administrador si el problema persiste.",
                "error_type": "InternalServerError",
                "details": {"message": str(e)}
            }
        )


@router.get(
    "/schema",
    summary="Get Database Schema",
    description="Get information about available tables and their structure"
)
async def get_schema(
    tables: Optional[List[str]] = None,
    query_service: QueryService = Depends(get_query_service)
) -> Dict[str, Any]:
    """Get database schema information."""
    try:
        schema_info = await query_service.get_database_schema(tables)
        return schema_info

    except Exception as e:
        logger.error(f"Error getting schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error al obtener información del esquema de la base de datos.",
                "error_type": "SchemaError",
                "details": {"message": str(e)}
            }
        )


@router.get(
    "/tables",
    summary="Get Available Tables",
    description="Get list of all available tables in the database"
)
async def get_tables(
    ai_service: AIService = Depends(get_ai_service)
) -> Dict[str, List[str]]:
    """Get list of available tables."""
    try:
        tables = ai_service.get_available_tables()
        return {"tables": tables}

    except Exception as e:
        logger.error(f"Error getting tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error al obtener la lista de tablas.",
                "error_type": "TablesError",
                "details": {"message": str(e)}
            }
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the service"
)
async def health_check(
    query_service: QueryService = Depends(get_query_service)
) -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        stats = query_service.get_query_statistics()
        return {
            "status": "healthy",
            "service": "intelligent_agent",
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "intelligent_agent",
            "error": str(e)
        }


@router.post(
    "/validate-sql",
    summary="Validate SQL Query",
    description="Validate if a SQL query is safe to execute"
)
async def validate_sql(
    sql_query: str,
    query_service: QueryService = Depends(get_query_service)
) -> Dict[str, Any]:
    """Validate SQL query safety."""
    try:
        is_safe, error_message = await query_service.validate_query_safety(sql_query)
        return {
            "is_safe": is_safe,
            "error_message": error_message,
            "query": sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
        }

    except Exception as e:
        logger.error(f"Error validating SQL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error al validar la consulta SQL.",
                "error_type": "ValidationError",
                "details": {"message": str(e)}
            }
        )