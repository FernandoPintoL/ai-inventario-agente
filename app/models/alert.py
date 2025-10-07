"""
Modelos para el sistema de alertas automáticas
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AlertaSeveridad:
    """Niveles de severidad de alertas"""
    CRITICO = "CRITICO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"


class ProductoAlerta(BaseModel):
    """Modelo de un producto con alerta de stock bajo"""
    producto_id: int
    producto_nombre: str
    producto_codigo: Optional[str] = None
    almacen_id: int
    almacen_nombre: str
    stock_actual: int  # cantidad_disponible
    stock_total: Optional[int] = None  # cantidad total
    stock_reservado: Optional[int] = None  # cantidad_reservada
    stock_minimo: int
    deficit: int
    porcentaje_stock: float = Field(..., description="Porcentaje del stock actual respecto al mínimo")
    severidad: str = Field(..., description="CRITICO, MEDIO, BAJO")

    @property
    def es_critico(self) -> bool:
        """Verifica si la alerta es crítica"""
        return self.severidad == AlertaSeveridad.CRITICO

    @property
    def es_medio(self) -> bool:
        """Verifica si la alerta es de nivel medio"""
        return self.severidad == AlertaSeveridad.MEDIO

    @property
    def es_bajo(self) -> bool:
        """Verifica si la alerta es de nivel bajo"""
        return self.severidad == AlertaSeveridad.BAJO


class AlertaAgrupada(BaseModel):
    """Modelo de alertas agrupadas para envío"""
    criticas: List[ProductoAlerta] = []
    medias: List[ProductoAlerta] = []
    bajas: List[ProductoAlerta] = []
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def total_alertas(self) -> int:
        """Total de alertas"""
        return len(self.criticas) + len(self.medias) + len(self.bajas)

    @property
    def tiene_criticas(self) -> bool:
        """Verifica si hay alertas críticas"""
        return len(self.criticas) > 0

    @property
    def tiene_alertas(self) -> bool:
        """Verifica si hay alertas para enviar"""
        return self.total_alertas > 0


class AlertaEnviada(BaseModel):
    """Modelo para registro de alerta enviada"""
    producto_id: int
    almacen_id: int
    severidad: str
    mensaje: str
    destinatarios: List[str]
    fecha_envio: datetime = Field(default_factory=datetime.now)
