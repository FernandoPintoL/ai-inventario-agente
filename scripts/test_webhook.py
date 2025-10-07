"""
Script de prueba para verificar conectividad con el webhook del sistema Laravel
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import requests
import json
from config.settings import settings

def test_webhook_ping():
    """Prueba el endpoint de ping"""
    url = settings.webhook_url.replace('/notificacion', '/ping')
    headers = {
        "X-Agente-Token": settings.webhook_token
    }

    print("="*70)
    print("TEST 1: PING ENDPOINT")
    print("="*70)
    print(f"URL: {url}")
    print(f"Token: {settings.webhook_token[:10]}...")
    print()

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[OK] Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print()
        return False


def test_webhook_notificacion_simple():
    """Prueba enviar una notificación simple"""
    url = settings.webhook_url
    headers = {
        "Content-Type": "application/json",
        "X-Agente-Token": settings.webhook_token
    }

    payload = {
        "tipo": "alerta_general",
        "titulo": "Test desde agente Python",
        "mensaje": "Mensaje de prueba simple"
    }

    print("="*70)
    print("TEST 2: NOTIFICACIÓN SIMPLE (solo campos requeridos)")
    print("="*70)
    print(f"URL: {url}")
    print(f"Token: {settings.webhook_token[:10]}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print()

        if response.status_code == 201:
            print("[OK] Notificacion simple enviada correctamente")
            data = response.json()
            print(f"Usuarios notificados: {data.get('usuarios_notificados', 0)}")
            return True
        else:
            print(f"[ERROR] Error al enviar notificacion")
            return False

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print()
        return False


def test_webhook_notificacion_completa():
    """Prueba enviar una notificación completa con todos los campos"""
    url = settings.webhook_url
    headers = {
        "Content-Type": "application/json",
        "X-Agente-Token": settings.webhook_token
    }

    payload = {
        "tipo": "alerta_general",
        "titulo": "Test Stock Bajo",
        "mensaje": "Prueba de notificación completa con datos",
        "prioridad": "alta",
        "url": "/inventario/stock-bajo",
        "data": {
            "total_alertas": 2,
            "alertas_criticas": 1,
            "alertas_medias": 1,
            "alertas_bajas": 0,
            "productos": [
                {
                    "producto_id": 1,
                    "producto_nombre": "Producto Test 1",
                    "almacen_id": 1,
                    "almacen_nombre": "Almacén Central",
                    "stock_actual": 5,
                    "stock_minimo": 50,
                    "deficit": 45,
                    "porcentaje_stock": 10.0,
                    "severidad": "critico"
                },
                {
                    "producto_id": 2,
                    "producto_nombre": "Producto Test 2",
                    "almacen_id": 1,
                    "almacen_nombre": "Almacén Central",
                    "stock_actual": 20,
                    "stock_minimo": 50,
                    "deficit": 30,
                    "porcentaje_stock": 40.0,
                    "severidad": "medio"
                }
            ]
        }
    }

    print("="*70)
    print("TEST 3: NOTIFICACIÓN COMPLETA (todos los campos)")
    print("="*70)
    print(f"URL: {url}")
    print(f"Token: {settings.webhook_token[:10]}...")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print()

        if response.status_code == 201:
            print("[OK] Notificacion completa enviada correctamente")
            data = response.json()
            print(f"Usuarios notificados: {data.get('usuarios_notificados', 0)}")
            return True
        else:
            print(f"[ERROR] Error al enviar notificacion")
            return False

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print()
        return False


def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("DIAGNOSTICO DE CONEXION CON WEBHOOK LARAVEL")
    print("="*70)
    print(f"Webhook URL: {settings.webhook_url}")
    print(f"Webhook Token: {settings.webhook_token}")
    print(f"Webhook Enabled: {settings.webhook_enabled}")
    print("="*70)
    print("\n")

    if not settings.webhook_enabled:
        print("ADVERTENCIA: El webhook esta DESHABILITADO en .env")
        print("   Para habilitarlo, configura: WEBHOOK_ENABLED=true")
        print("\n")
        respuesta = input("Continuar con las pruebas de todos modos? (s/n): ")
        if respuesta.lower() != 's':
            return
        print("\n")

    # Test 1: Ping
    ping_ok = test_webhook_ping()

    # Test 2: Notificación simple
    if ping_ok:
        simple_ok = test_webhook_notificacion_simple()
    else:
        print("[SKIP] Saltando Test 2 porque el ping falló\n")
        simple_ok = False

    # Test 3: Notificación completa
    if simple_ok:
        completa_ok = test_webhook_notificacion_completa()
    else:
        print("[SKIP] Saltando Test 3 porque el test simple falló\n")
        completa_ok = False

    # Resumen
    print("="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    print(f"1. Ping Endpoint:          {'[OK]' if ping_ok else '[FALLO]'}")
    print(f"2. Notificacion Simple:    {'[OK]' if simple_ok else '[FALLO]'}")
    print(f"3. Notificacion Completa:  {'[OK]' if completa_ok else '[FALLO]'}")
    print("="*70)

    if ping_ok and simple_ok and completa_ok:
        print("\n[OK] Todas las pruebas pasaron. El webhook esta funcionando correctamente.\n")
    else:
        print("\n[ERROR] Algunas pruebas fallaron. Revisa la configuracion:\n")
        print("Posibles causas:")
        print("  1. El token en .env no coincide con el del sistema Laravel")
        print("  2. La URL del webhook es incorrecta")
        print("  3. El servidor Laravel no esta accesible")
        print("  4. No hay usuarios con los roles especificados en Laravel")
        print("  5. Firewall o restriccion de red\n")


if __name__ == "__main__":
    main()
