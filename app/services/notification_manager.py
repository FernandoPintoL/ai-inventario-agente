"""
Notification Manager - Envío de notificaciones por email usando SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from datetime import datetime
import json
import requests

from app.models.alert import AlertaAgrupada, ProductoAlerta
from app.database import db_manager
from app.core.logging import get_logger
from config.settings import settings

logger = get_logger("notification_manager")


class NotificationManager:
    """Gestor de notificaciones de alertas"""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.alert_email_from
        self.to_emails = settings.alert_email_to
        self.db = db_manager

        # Configuración webhook
        self.webhook_url = settings.webhook_url
        self.webhook_token = settings.webhook_token
        self.webhook_enabled = settings.webhook_enabled

    def enviar_alertas(self, alertas: AlertaAgrupada) -> bool:
        """
        Envía alertas agrupadas por email

        Args:
            alertas: Alertas agrupadas para enviar

        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not alertas.tiene_alertas:
            logger.info("No hay alertas para enviar")
            return True

        try:
            logger.info(
                f"Enviando alertas: {len(alertas.criticas)} críticas, "
                f"{len(alertas.medias)} medias, {len(alertas.bajas)} bajas"
            )

            # Generar contenido del email
            asunto = self._generar_asunto(alertas)
            contenido_html = self._generar_contenido_html(alertas)
            contenido_texto = self._generar_contenido_texto(alertas)

            # Enviar email
            exito = self._enviar_email(asunto, contenido_html, contenido_texto)

            if exito:
                # Registrar alertas enviadas
                self._registrar_alertas_enviadas(alertas)
                logger.info("Alertas enviadas y registradas correctamente")

                # Enviar webhook a Laravel (si está habilitado)
                self._enviar_webhook(alertas, asunto)
            else:
                logger.error("Error al enviar alertas")

            return exito

        except Exception as e:
            logger.error(f"Error al enviar alertas: {e}")
            return False

    def _generar_asunto(self, alertas: AlertaAgrupada) -> str:
        """Genera el asunto del email según severidad"""
        total = alertas.total_alertas

        if alertas.tiene_criticas:
            return f"⚠️ ALERTA CRÍTICA: {len(alertas.criticas)} productos con stock muy bajo"
        elif len(alertas.medias) > 0:
            return f"⚠️ ALERTA: {total} productos con stock bajo"
        else:
            return f"📊 Aviso: {total} productos cerca del stock mínimo"

    def _generar_contenido_html(self, alertas: AlertaAgrupada) -> str:
        """Genera contenido HTML del email"""
        fecha = alertas.timestamp.strftime("%d/%m/%Y %H:%M")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .alert-section {{ margin-bottom: 30px; }}
                .critico {{ color: #dc3545; font-weight: bold; }}
                .medio {{ color: #fd7e14; font-weight: bold; }}
                .bajo {{ color: #ffc107; font-weight: bold; }}
                .producto {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #ccc;
                }}
                .producto.critico {{ border-left-color: #dc3545; }}
                .producto.medio {{ border-left-color: #fd7e14; }}
                .producto.bajo {{ border-left-color: #ffc107; }}
                .detalle {{ margin: 5px 0; }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔔 Alerta de Inventario</h2>
                <p><strong>Fecha:</strong> {fecha}</p>
                <p><strong>Total de alertas:</strong> {alertas.total_alertas}</p>
            </div>
        """

        # Alertas críticas
        if alertas.criticas:
            html += self._generar_seccion_html(
                "🔴 PRODUCTOS CRÍTICOS (Stock < 20%)",
                alertas.criticas,
                "critico"
            )

        # Alertas medias
        if alertas.medias:
            html += self._generar_seccion_html(
                "🟠 PRODUCTOS NIVEL MEDIO (Stock < 50%)",
                alertas.medias,
                "medio"
            )

        # Alertas bajas
        if alertas.bajas:
            html += self._generar_seccion_html(
                "🟡 PRODUCTOS NIVEL BAJO (Stock < 100%)",
                alertas.bajas,
                "bajo"
            )

        html += """
            <div class="footer">
                <p>🤖 Este es un mensaje automático generado por el Agente Inteligente de Inventario.</p>
                <p>Por favor, tome las acciones necesarias para reponer el stock de los productos indicados.</p>
            </div>
        </body>
        </html>
        """

        return html

    def _generar_seccion_html(
        self,
        titulo: str,
        productos: List[ProductoAlerta],
        clase: str
    ) -> str:
        """Genera una sección HTML para una lista de productos"""
        html = f"""
        <div class="alert-section">
            <h3 class="{clase}">{titulo}</h3>
        """

        for producto in productos:
            # Preparar información de stock
            stock_info = f"<div class=\"detalle\">📦 Stock disponible: <strong>{producto.stock_actual}</strong> unidades ({producto.porcentaje_stock:.1f}% del mínimo)</div>"

            # Agregar info de stock reservado si existe
            if producto.stock_reservado and producto.stock_reservado > 0:
                stock_info += f"<div class=\"detalle\">🔒 Stock reservado: {producto.stock_reservado} unidades</div>"
                stock_info += f"<div class=\"detalle\">📊 Stock total: {producto.stock_total} unidades</div>"

            html += f"""
            <div class="producto {clase}">
                <div class="detalle"><strong>{producto.producto_nombre}</strong></div>
                {stock_info}
                <div class="detalle">⚠️ Stock mínimo: {producto.stock_minimo} unidades</div>
                <div class="detalle">📉 Déficit: <strong>{producto.deficit}</strong> unidades</div>
                <div class="detalle">🏢 Almacén: {producto.almacen_nombre}</div>
            </div>
            """

        html += "</div>"
        return html

    def _generar_contenido_texto(self, alertas: AlertaAgrupada) -> str:
        """Genera contenido en texto plano del email"""
        fecha = alertas.timestamp.strftime("%d/%m/%Y %H:%M")

        texto = f"""
ALERTA DE INVENTARIO
Fecha: {fecha}
Total de alertas: {alertas.total_alertas}

{'='*60}
"""

        if alertas.criticas:
            texto += "\n🔴 PRODUCTOS CRÍTICOS (Stock < 20%):\n"
            texto += "="*60 + "\n"
            for producto in alertas.criticas:
                texto += self._generar_producto_texto(producto)

        if alertas.medias:
            texto += "\n🟠 PRODUCTOS NIVEL MEDIO (Stock < 50%):\n"
            texto += "="*60 + "\n"
            for producto in alertas.medias:
                texto += self._generar_producto_texto(producto)

        if alertas.bajas:
            texto += "\n🟡 PRODUCTOS NIVEL BAJO (Stock < 100%):\n"
            texto += "="*60 + "\n"
            for producto in alertas.bajas:
                texto += self._generar_producto_texto(producto)

        texto += "\n" + "="*60 + "\n"
        texto += "🤖 Mensaje automático del Agente Inteligente de Inventario\n"

        return texto

    def _generar_producto_texto(self, producto: ProductoAlerta) -> str:
        """Genera texto para un producto"""
        texto = f"""
• {producto.producto_nombre}
  Stock disponible: {producto.stock_actual} unidades ({producto.porcentaje_stock:.1f}%)
"""
        # Agregar info de stock reservado si existe
        if producto.stock_reservado and producto.stock_reservado > 0:
            texto += f"  Stock reservado: {producto.stock_reservado} unidades\n"
            texto += f"  Stock total: {producto.stock_total} unidades\n"

        texto += f"""  Stock mínimo: {producto.stock_minimo} unidades
  Déficit: {producto.deficit} unidades
  Almacén: {producto.almacen_nombre}

"""
        return texto

    def _enviar_email(self, asunto: str, html: str, texto: str) -> bool:
        """
        Envía email usando SMTP

        Args:
            asunto: Asunto del email
            html: Contenido HTML
            texto: Contenido en texto plano

        Returns:
            True si se envió correctamente
        """
        try:
            # Crear mensaje
            mensaje = MIMEMultipart('alternative')
            mensaje['Subject'] = asunto
            mensaje['From'] = self.from_email
            mensaje['To'] = ', '.join(self.to_emails)

            # Agregar contenido
            parte_texto = MIMEText(texto, 'plain', 'utf-8')
            parte_html = MIMEText(html, 'html', 'utf-8')

            mensaje.attach(parte_texto)
            mensaje.attach(parte_html)

            # Enviar via SMTP
            logger.info(f"Conectando a {self.smtp_host}:{self.smtp_port}")

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Activar TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(mensaje)

            logger.info(f"Email enviado correctamente a: {', '.join(self.to_emails)}")
            return True

        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            return False

    def _registrar_alertas_enviadas(self, alertas: AlertaAgrupada):
        """
        Registra alertas enviadas en la base de datos para spam control

        Args:
            alertas: Alertas que fueron enviadas
        """
        try:
            query = """
            INSERT INTO alertas_enviadas
                (producto_id, almacen_id, severidad, mensaje, destinatarios)
            VALUES (%s, %s, %s, %s, %s)
            """

            registros = []

            # Preparar todos los registros
            for producto in alertas.criticas + alertas.medias + alertas.bajas:
                registros.append((
                    producto.producto_id,
                    producto.almacen_id,
                    producto.severidad,
                    f"Stock bajo: {producto.stock_actual}/{producto.stock_minimo}",
                    json.dumps(self.to_emails)
                ))

            # Insertar en batch
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(query, registros)
                conn.commit()

            logger.info(f"Registradas {len(registros)} alertas en la base de datos")

        except Exception as e:
            logger.error(f"Error al registrar alertas enviadas: {e}")

    def _enviar_webhook(self, alertas: AlertaAgrupada, asunto: str) -> bool:
        """
        Envía notificación webhook al sistema Laravel

        Args:
            alertas: Alertas agrupadas
            asunto: Asunto del email enviado

        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not self.webhook_enabled:
            logger.debug("Webhook deshabilitado, omitiendo envío")
            return False

        if not self.webhook_url or not self.webhook_token:
            logger.warning("Webhook habilitado pero falta configuración (URL o Token)")
            return False

        try:
            # Determinar el tipo de notificación según la severidad
            if alertas.tiene_criticas:
                tipo = "stock_bajo"
                prioridad = "alta"
            elif len(alertas.medias) > 0:
                tipo = "stock_bajo"
                prioridad = "media"
            else:
                tipo = "stock_bajo"
                prioridad = "baja"

            # Preparar datos adicionales con información de productos
            productos_data = []
            for producto in alertas.criticas + alertas.medias + alertas.bajas:
                productos_data.append({
                    "producto_id": producto.producto_id,
                    "producto_nombre": producto.producto_nombre,
                    "almacen_id": producto.almacen_id,
                    "almacen_nombre": producto.almacen_nombre,
                    "stock_actual": producto.stock_actual,
                    "stock_minimo": producto.stock_minimo,
                    "deficit": producto.deficit,
                    "porcentaje_stock": float(producto.porcentaje_stock),
                    "severidad": producto.severidad
                })

            # Generar mensaje descriptivo
            mensaje = self._generar_mensaje_webhook(alertas)

            # Preparar payload según formato de la documentación
            payload = {
                "tipo": tipo,
                "titulo": asunto.replace("⚠️", "").replace("📊", "").strip(),
                "mensaje": mensaje,
                "prioridad": prioridad,
                "url": "/inventario/stock-bajo",
                "data": {
                    "total_alertas": alertas.total_alertas,
                    "alertas_criticas": len(alertas.criticas),
                    "alertas_medias": len(alertas.medias),
                    "alertas_bajas": len(alertas.bajas),
                    "productos": productos_data,
                    "timestamp": alertas.timestamp.isoformat()
                }
                # roles: omitido intencionalmente para que Laravel use los roles por defecto del tipo
            }

            # Headers según documentación
            headers = {
                "Content-Type": "application/json",
                "X-Agente-Token": self.webhook_token
            }

            # Log detallado para debugging
            logger.info("="*60)
            logger.info("ENVIANDO WEBHOOK AL SISTEMA EXTERNO")
            logger.info(f"URL: {self.webhook_url}")
            logger.info(f"Token (primeros 10 chars): {self.webhook_token[:10]}...")
            logger.info(f"Payload completo:")
            logger.info(f"  - tipo: {payload['tipo']}")
            logger.info(f"  - titulo: {payload['titulo']}")
            logger.info(f"  - mensaje: {payload['mensaje']}")
            logger.info(f"  - prioridad: {payload['prioridad']}")
            logger.info(f"  - roles: {payload.get('roles', 'omitido - usa roles por defecto')}")
            logger.info(f"  - total productos: {len(productos_data)}")
            logger.info(f"Payload JSON completo: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            logger.info("="*60)

            # Enviar petición POST
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )

            # Log de respuesta
            logger.info(f"Respuesta del servidor:")
            logger.info(f"  - Status Code: {response.status_code}")
            logger.info(f"  - Headers: {dict(response.headers)}")
            logger.info(f"  - Body: {response.text}")

            # Verificar respuesta
            if response.status_code == 201:
                data = response.json()
                usuarios_notificados = data.get("usuarios_notificados", 0)
                logger.info(f"✅ Webhook enviado exitosamente. Usuarios notificados: {usuarios_notificados}")
                return True
            else:
                logger.error(f"❌ Error al enviar webhook. Status: {response.status_code}")
                logger.error(f"Response completo: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Timeout al enviar webhook")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión al enviar webhook")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al enviar webhook: {e}")
            return False

    def _generar_mensaje_webhook(self, alertas: AlertaAgrupada) -> str:
        """
        Genera mensaje descriptivo para el webhook

        Args:
            alertas: Alertas agrupadas

        Returns:
            Mensaje descriptivo
        """
        partes = []

        if alertas.criticas:
            partes.append(f"{len(alertas.criticas)} producto(s) con stock crítico (< 20%)")

        if alertas.medias:
            partes.append(f"{len(alertas.medias)} producto(s) con stock bajo (< 50%)")

        if alertas.bajas:
            partes.append(f"{len(alertas.bajas)} producto(s) cerca del stock mínimo (< 100%)")

        return " • ".join(partes) if partes else "Productos con stock bajo detectados"


# Instancia global
notification_manager = NotificationManager()
