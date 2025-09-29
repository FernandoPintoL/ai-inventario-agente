#!/usr/bin/env python3
"""
Script de prueba para operaciones INSERT, UPDATE, DELETE
"""
import requests
import json

BASE_URL = "http://localhost:8080/api/v1"

def test_query(description: str, query: str):
    """Ejecuta una consulta y muestra el resultado."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    print(f"Query: {query}")

    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={"human_query": query},
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ SUCCESS")
            print(f"Answer: {data.get('answer', 'N/A')}")
            print(f"SQL Query: {data.get('sql_query', 'N/A')}")
            print(f"Execution Time: {data.get('execution_time', 'N/A')}s")
            if data.get('raw_data'):
                print(f"Raw Data: {json.dumps(data['raw_data'], indent=2)}")
        else:
            print(f"\n✗ FAILED")
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")

def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "="*60)
    print("PRUEBAS DE OPERACIONES DE BASE DE DATOS")
    print("="*60)

    # Test 1: SELECT (para ver datos existentes)
    test_query(
        "SELECT - Ver categorías existentes",
        "muéstrame todas las categorías"
    )

    # Test 2: INSERT
    test_query(
        "INSERT - Insertar nueva categoría",
        "inserta en categoría el nombre 'Agua con gas'"
    )

    # Test 3: SELECT para verificar INSERT
    test_query(
        "SELECT - Verificar inserción",
        "muéstrame la categoría 'Agua con gas'"
    )

    # Test 4: UPDATE
    test_query(
        "UPDATE - Actualizar categoría",
        "actualiza la categoría 'Agua con gas' cambia el nombre a 'Bebidas con gas'"
    )

    # Test 5: SELECT para verificar UPDATE
    test_query(
        "SELECT - Verificar actualización",
        "muéstrame la categoría 'Bebidas con gas'"
    )

    # Test 6: DELETE
    test_query(
        "DELETE - Eliminar categoría",
        "elimina la categoría 'Bebidas con gas'"
    )

    # Test 7: SELECT para verificar DELETE
    test_query(
        "SELECT - Verificar eliminación",
        "muéstrame la categoría 'Bebidas con gas'"
    )

    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()