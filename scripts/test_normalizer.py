"""
Script de Prueba Rapida del Text Normalizer
============================================
Script para probar manualmente el normalizador de texto con consultas de ejemplo.
"""

import sys
import os
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Agregar el directorio raiz al path para importar modulos
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.services.text_normalizer import TextNormalizer


def print_separator(char="=", length=80):
    """Imprime una línea separadora"""
    print(char * length)


def print_section_header(title):
    """Imprime un encabezado de sección"""
    print_separator()
    print(f" {title}")
    print_separator()


def test_normalization_examples():
    """Prueba ejemplos de normalización"""
    print_section_header("PRUEBAS DE NORMALIZACIÓN DE TEXTO")

    # Inicializar el normalizador
    print("\n📦 Inicializando Text Normalizer...")
    normalizer = TextNormalizer()
    print("✅ Normalizer inicializado correctamente\n")

    # Ejemplos de consultas del usuario
    test_queries = [
        # Singular a plural
        ("cuantos producto hay en el sistema", "❌ Singular -> ✅ Plural"),
        ("dame todas las categoria activas", "❌ Singular -> ✅ Plural"),
        ("muestra el almacen principal", "❌ Singular -> ✅ Plural"),

        # Sinónimos comunes
        ("cuantas bodegas tenemos", "❌ Sinónimo 'bodega' -> ✅ 'almacenes'"),
        ("lista los articulos disponibles", "❌ Sinónimo 'articulos' -> ✅ 'productos'"),
        ("muestra el inventario actual", "❌ Sinónimo 'inventario' -> ✅ 'stock_productos'"),

        # Errores ortográficos
        ("dame las categria", "❌ Error ortográfico -> ✅ Corregido"),
        ("lista los porductos", "❌ Error ortográfico -> ✅ Corregido"),

        # Múltiples tablas
        ("dame los producto de cada categoria en el almacen", "❌ Múltiples errores -> ✅ Corregido"),

        # Consultas complejas reales
        ("cuantos articulos hay en cada bodega", "❌ Consulta compleja -> ✅ Normalizada"),
        ("muestra el precio de los producto por categoria", "❌ Consulta compleja -> ✅ Normalizada"),
        ("que tipo de merma hay registradas", "❌ Consulta compleja -> ✅ Normalizada"),
    ]

    print_section_header("RESULTADOS DE NORMALIZACIÓN")

    for i, (query, description) in enumerate(test_queries, 1):
        print(f"\n{i}. {description}")
        print(f"   Original:    '{query}'")

        # Normalizar la consulta
        normalized = normalizer.normalize_query(query, enable_fuzzy=True)

        print(f"   Normalizado: '{normalized}'")

        # Indicar si hubo cambios
        if normalized != query:
            print(f"   📊 Status: ✅ NORMALIZADA")
        else:
            print(f"   📊 Status: ⚠️  Sin cambios")

        print("-" * 80)


def test_statistics():
    """Muestra estadísticas del normalizador"""
    print_section_header("ESTADÍSTICAS DEL NORMALIZADOR")

    normalizer = TextNormalizer()
    stats = normalizer.get_statistics()

    print(f"\n📊 Total de tablas:           {stats['total_tables']}")
    print(f"📊 Total de sinónimos:        {stats['total_table_synonyms']}")
    print(f"📊 Sinónimos de columnas:     {stats['total_column_synonyms']}")
    print(f"📊 Versión del diccionario:   {stats['dictionary_version']}")
    print(f"📊 Umbral fuzzy matching:     {stats['fuzzy_threshold']}")
    print(f"📊 Distancia máxima fuzzy:    {stats['max_fuzzy_distance']}")
    print()


def test_table_list():
    """Muestra la lista de tablas disponibles"""
    print_section_header("TABLAS DISPONIBLES EN LA BASE DE DATOS")

    normalizer = TextNormalizer()
    tables = normalizer.get_all_table_names()

    print(f"\n📋 Total: {len(tables)} tablas\n")
    for i, table in enumerate(tables, 1):
        print(f"  {i:2d}. {table}")
    print()


def test_interactive_mode():
    """Modo interactivo para probar consultas personalizadas"""
    print_section_header("MODO INTERACTIVO")

    normalizer = TextNormalizer()

    print("\n💡 Ingresa consultas para normalizarlas")
    print("💡 Escribe 'salir' o 'exit' para terminar\n")

    while True:
        try:
            query = input("Tu consulta: ").strip()

            if not query:
                continue

            if query.lower() in ['salir', 'exit', 'quit', 'q']:
                print("\n👋 ¡Hasta luego!")
                break

            # Normalizar
            normalized = normalizer.normalize_query(query, enable_fuzzy=True)

            print(f"Normalizado: '{normalized}'")

            if normalized != query:
                print("✅ Se aplicaron correcciones")
            else:
                print("⚠️  No se encontraron correcciones")

            print()

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


def main():
    """Función principal"""
    print()
    print("=" * 80)
    print(" " * 20 + "TEXT NORMALIZER - PRUEBAS")
    print("=" * 80)
    print()

    try:
        # Ejecutar pruebas automáticas
        test_normalization_examples()
        test_statistics()
        test_table_list()

        # Preguntar si quiere modo interactivo
        print_separator()
        response = input("\n¿Deseas probar el modo interactivo? (s/n): ").strip().lower()

        if response in ['s', 'si', 'y', 'yes']:
            print()
            test_interactive_mode()
        else:
            print("\n✅ Pruebas completadas exitosamente!")

    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
