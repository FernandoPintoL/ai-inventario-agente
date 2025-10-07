#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el sistema de alertas automáticas
Ejecuta manualmente la detección y envío de alertas sin esperar al scheduler
"""
import sys
import os
import io

# Configurar encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.alert_detector import alert_detector
from app.services.notification_manager import notification_manager
from app.core.logging import setup_logging, get_logger

# Configurar logging
setup_logging()
logger = get_logger("test_alertas")


def main():
    """Ejecuta una prueba completa del sistema de alertas"""

    print("="*60)
    print("🧪 PRUEBA DEL SISTEMA DE ALERTAS AUTOMÁTICAS")
    print("="*60)
    print()

    # 1. Detectar stock bajo
    print("📊 Paso 1: Detectando productos con stock bajo...")
    print("-"*60)

    try:
        alertas = alert_detector.detectar_stock_bajo()

        print(f"✅ Detección completada")
        print(f"   Total de alertas: {alertas.total_alertas}")
        print(f"   - 🔴 Críticas: {len(alertas.criticas)}")
        print(f"   - 🟠 Medias: {len(alertas.medias)}")
        print(f"   - 🟡 Bajas: {len(alertas.bajas)}")
        print()

        # Mostrar detalles de alertas críticas
        if alertas.criticas:
            print("🔴 ALERTAS CRÍTICAS:")
            for producto in alertas.criticas:
                print(f"   • {producto.producto_nombre}")
                print(f"     Stock: {producto.stock_actual}/{producto.stock_minimo} "
                      f"({producto.porcentaje_stock:.1f}%)")
                print(f"     Almacén: {producto.almacen_nombre}")
            print()

        # 2. Enviar notificación si hay alertas
        if alertas.tiene_alertas:
            print("📧 Paso 2: Enviando notificaciones...")
            print("-"*60)

            respuesta = input("¿Deseas enviar el email de prueba? (s/n): ")

            if respuesta.lower() == 's':
                exito = notification_manager.enviar_alertas(alertas)

                if exito:
                    print("✅ Email enviado correctamente")
                    print("   Verifica tu bandeja de entrada")
                else:
                    print("❌ Error al enviar email")
                    print("   Revisa los logs para más detalles")
            else:
                print("⏭️  Envío de email omitido")
        else:
            print("ℹ️  No hay alertas para enviar")
            print("   Todos los productos tienen stock suficiente")

        print()
        print("="*60)
        print("✅ PRUEBA COMPLETADA")
        print("="*60)

    except Exception as e:
        logger.error(f"Error en prueba: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        print("   Revisa los logs en logs/app.log")
        sys.exit(1)


if __name__ == "__main__":
    main()
