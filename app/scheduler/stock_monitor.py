"""
Stock Monitor - Scheduler para monitoreo automático de stock
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.services.alert_detector import alert_detector
from app.services.notification_manager import notification_manager
from app.core.logging import get_logger
from config.settings import settings

logger = get_logger("stock_monitor")
class StockMonitor:
    """Monitor automático de stock con scheduler"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.intervalo_minutos = settings.alert_check_interval
        self.is_running = False

    def verificar_stock(self):
        """
        Función que se ejecuta periódicamente para verificar stock

        Este es el corazón del sistema de alertas automáticas:
        1. Detecta productos con stock bajo
        2. Clasifica por severidad
        3. Filtra spam (no enviar duplicados)
        4. Envía notificaciones si hay alertas
        """
        try:
            logger.info("="*60)
            logger.info(f"Iniciando verificación automática de stock - {datetime.now()}")
            logger.info("="*60)

            # 1. Detectar stock bajo
            alertas = alert_detector.detectar_stock_bajo()

            # 2. Si hay alertas, enviar notificación
            if alertas.tiene_alertas:
                logger.info(
                    f"Se detectaron {alertas.total_alertas} alertas: "
                    f"{len(alertas.criticas)} críticas, "
                    f"{len(alertas.medias)} medias, "
                    f"{len(alertas.bajas)} bajas"
                )

                # Enviar notificaciones
                exito = notification_manager.enviar_alertas(alertas)

                if exito:
                    logger.info("✅ Notificaciones enviadas correctamente")
                else:
                    logger.error("❌ Error al enviar notificaciones")
            else:
                logger.info("✅ No se detectaron productos con stock bajo")

            logger.info("="*60)
            logger.info("Verificación completada")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Error en verificación automática: {e}", exc_info=True)

    def start(self):
        """Inicia el scheduler"""
        if self.is_running:
            logger.warning("El scheduler ya está en ejecución")
            return

        try:
            # Configurar job
            self.scheduler.add_job(
                func=self.verificar_stock,
                trigger=IntervalTrigger(minutes=self.intervalo_minutos),
                id='stock_monitor',
                name='Verificación automática de stock',
                replace_existing=True,
                max_instances=1  # Solo una instancia a la vez
            )

            # Iniciar scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("="*60)
            logger.info("🚀 SCHEDULER DE ALERTAS INICIADO")
            logger.info(f"Intervalo de verificación: cada {self.intervalo_minutos} minutos")
            logger.info(f"Próxima ejecución: {datetime.now()}")
            logger.info("="*60)

            # Ejecutar inmediatamente la primera verificación (opcional)
            if settings.alert_run_on_startup:
                logger.info("Ejecutando verificación inicial...")
                self.verificar_stock()

        except Exception as e:
            logger.error(f"Error al iniciar scheduler: {e}")
            raise

    def stop(self):
        """Detiene el scheduler"""
        if not self.is_running:
            logger.warning("El scheduler no está en ejecución")
            return

        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("🛑 Scheduler de alertas detenido")

        except Exception as e:
            logger.error(f"Error al detener scheduler: {e}")

    def get_status(self) -> dict:
        """Obtiene el estado actual del scheduler"""
        if not self.is_running:
            return {
                "running": False,
                "jobs": []
            }

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            })

        return {
            "running": True,
            "interval_minutes": self.intervalo_minutos,
            "jobs": jobs
        }


# Instancia global del monitor
stock_scheduler = StockMonitor()
