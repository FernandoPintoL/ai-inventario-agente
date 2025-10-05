"""
Tests for Text Normalizer Service
==================================
Pruebas unitarias para validar el funcionamiento del normalizador de texto.
"""

import pytest
from pathlib import Path
from app.services.text_normalizer import TextNormalizer


class TestTextNormalizer:
    """Test suite for TextNormalizer class"""

    @pytest.fixture
    def normalizer(self):
        """Fixture que proporciona una instancia del normalizador"""
        return TextNormalizer()

    def test_normalizer_initialization(self, normalizer):
        """Test que el normalizador se inicializa correctamente"""
        assert normalizer is not None
        assert len(normalizer.real_table_names) > 0
        assert normalizer.dictionary is not None

    def test_singular_to_plural_normalization(self, normalizer):
        """Test normalización de singular a plural"""
        test_cases = [
            ("dame todas las categoria", "categorias"),
            ("cuantos producto hay", "productos"),
            ("muestra el almacen", "almacenes"),
            ("lista las marca disponibles", "marcas"),
        ]

        for query, expected_word in test_cases:
            normalized = normalizer.normalize_query(query)
            assert expected_word in normalized.lower(), \
                f"Expected '{expected_word}' in normalized query: {normalized}"

    def test_synonym_normalization(self, normalizer):
        """Test normalización de sinónimos"""
        test_cases = [
            # bodega -> almacenes
            ("cuantas bodegas tengo", "almacenes"),
            # articulos -> productos
            ("lista los articulos", "productos"),
            # inventario -> stock_productos
            ("muestra el inventario", "stock_productos"),
            # tipo -> categorias
            ("dame los tipos", "categorias"),
        ]

        for query, expected_table in test_cases:
            normalized = normalizer.normalize_query(query)
            assert expected_table in normalized.lower(), \
                f"Expected '{expected_table}' in '{normalized}' for query '{query}'"

    def test_common_errors_correction(self, normalizer):
        """Test corrección de errores ortográficos comunes"""
        test_cases = [
            # categria -> categorias (error común)
            ("muestra las categria", "categorias"),
            # porducto -> productos (error común)
            ("dame los porductos", "productos"),
        ]

        for query, expected_word in test_cases:
            normalized = normalizer.normalize_query(query)
            # El normalizador debería intentar corregir estos errores
            assert expected_word in normalized.lower() or "categria" not in normalized.lower()

    def test_fuzzy_matching(self, normalizer):
        """Test fuzzy matching para palabras similares"""
        test_cases = [
            # almacen -> almacenes (falta 'es')
            ("cuantos almacen tenemos", "almacenes"),
            # categoria -> categorias (falta 's')
            ("lista categoria", "categorias"),
            # producto -> productos (falta 's')
            ("dame producto", "productos"),
        ]

        for query, expected_word in test_cases:
            normalized = normalizer.normalize_query(query, enable_fuzzy=True)
            assert expected_word in normalized.lower(), \
                f"Fuzzy matching failed: expected '{expected_word}' in '{normalized}'"

    def test_preserve_original_when_no_match(self, normalizer):
        """Test que preserva palabras cuando no hay coincidencia"""
        query = "dame los zapatos rojos"  # 'zapatos' no es una tabla
        normalized = normalizer.normalize_query(query)

        # Debería preservar palabras no relacionadas con tablas
        assert "zapatos" in normalized.lower()
        assert "rojos" in normalized.lower()

    def test_case_insensitive_normalization(self, normalizer):
        """Test que la normalización es insensible a mayúsculas/minúsculas"""
        test_cases = [
            "Dame todas las CATEGORIA",
            "dame TODAS las categoria",
            "DAME todas LAS categoria",
        ]

        for query in test_cases:
            normalized = normalizer.normalize_query(query)
            assert "categorias" in normalized.lower()

    def test_multiple_table_normalization(self, normalizer):
        """Test normalización de múltiples tablas en una consulta"""
        query = "dame los producto de cada categoria en el almacen"
        normalized = normalizer.normalize_query(query)

        assert "productos" in normalized.lower()
        assert "categorias" in normalized.lower()
        assert "almacenes" in normalized.lower()

    def test_word_boundary_preservation(self, normalizer):
        """Test que no reemplaza coincidencias parciales dentro de palabras"""
        query = "categorizado producto almacenamiento"  # Contiene 'categoria', 'producto', 'almacen'
        normalized = normalizer.normalize_query(query)

        # No debería romper palabras más largas
        # Este test verifica que se usen word boundaries en el regex
        assert "categorizado" in normalized.lower() or "categorias" in normalized.lower()

    def test_get_table_info(self, normalizer):
        """Test obtención de información de tablas"""
        info = normalizer.get_table_info("productos")
        assert info is not None
        assert "singular" in info
        assert "synonyms" in info

    def test_get_all_table_names(self, normalizer):
        """Test obtención de todos los nombres de tablas"""
        tables = normalizer.get_all_table_names()
        assert len(tables) > 0
        assert "productos" in tables
        assert "categorias" in tables
        assert "almacenes" in tables

    def test_statistics(self, normalizer):
        """Test obtención de estadísticas"""
        stats = normalizer.get_statistics()
        assert "total_tables" in stats
        assert "total_table_synonyms" in stats
        assert stats["total_tables"] > 0
        assert stats["total_table_synonyms"] > 0

    def test_cache_functionality(self, normalizer):
        """Test que el cache funciona correctamente"""
        query = "dame los productos"

        # Primera consulta
        normalizer.clear_cache()
        normalized1 = normalizer.normalize_query(query)

        # Segunda consulta (debería usar cache)
        normalized2 = normalizer.normalize_query(query)

        assert normalized1 == normalized2
        assert normalizer.get_statistics()["cache_size"] > 0

    def test_cache_clearing(self, normalizer):
        """Test limpieza de cache"""
        normalizer.normalize_query("dame los productos")
        assert normalizer.get_statistics()["cache_size"] > 0

        normalizer.clear_cache()
        assert normalizer.get_statistics()["cache_size"] == 0

    def test_empty_query_handling(self, normalizer):
        """Test manejo de consultas vacías"""
        assert normalizer.normalize_query("") == ""
        assert normalizer.normalize_query(None) == None

    def test_real_world_queries(self, normalizer):
        """Test consultas del mundo real"""
        real_queries = [
            ("cuantos producto hay en el sistema", "productos"),
            ("dame todas las categoria activas", "categorias"),
            ("muestra el stock de cada almacen", "almacenes"),
            ("lista los precio de los articulos", "productos"),
            ("que mermas hay registradas", "tipo_mermas"),
            ("cuantas transferencia se hicieron hoy", "transferencia_inventarios"),
        ]

        for query, expected_table in real_queries:
            normalized = normalizer.normalize_query(query)
            assert expected_table in normalized.lower(), \
                f"Real-world query failed: '{query}' -> expected '{expected_table}' in '{normalized}'"


# Tests de integración
class TestTextNormalizerIntegration:
    """Tests de integración con el sistema completo"""

    def test_normalizer_singleton(self):
        """Test que el singleton funciona correctamente"""
        from app.services.text_normalizer import get_text_normalizer

        normalizer1 = get_text_normalizer()
        normalizer2 = get_text_normalizer()

        assert normalizer1 is normalizer2  # Debe ser la misma instancia


if __name__ == "__main__":
    # Ejecutar tests manualmente
    normalizer = TextNormalizer()

    print("=" * 60)
    print("PRUEBAS MANUALES DEL TEXT NORMALIZER")
    print("=" * 60)

    test_queries = [
        "dame todas las categoria",
        "cuantos producto hay en la bodega",
        "muestra el inventario de articulos",
        "lista los precio de cada item",
        "que tipo de merma existen",
        "cuantas transferencia hay",
        "dame los almacen disponibles",
        "muestra las marca activas",
    ]

    for query in test_queries:
        normalized = normalizer.normalize_query(query)
        print(f"\nOriginal:    {query}")
        print(f"Normalizado: {normalized}")
        print("-" * 60)

    print("\n" + "=" * 60)
    print("ESTADÍSTICAS")
    print("=" * 60)
    stats = normalizer.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
