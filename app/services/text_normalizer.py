"""
Text Normalizer Service
=======================
Servicio para normalizar consultas en lenguaje natural usando un diccionario de sinónimos.

Este módulo proporciona:
- Normalización de nombres de tablas (singular/plural, sinónimos, errores comunes)
- Normalización de nombres de columnas
- Fuzzy matching como respaldo
- Cache para optimizar rendimiento
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple, Set
from difflib import SequenceMatcher
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger("text_normalizer")


class TextNormalizer:
    """
    Normaliza consultas en lenguaje natural reemplazando sinónimos y variaciones
    de nombres de tablas y columnas por sus nombres reales en la base de datos.
    """

    def __init__(self, dictionary_path: Optional[str] = None):
        """
        Inicializa el normalizador de texto.

        Args:
            dictionary_path: Ruta al archivo JSON con el diccionario de sinónimos.
                           Si no se proporciona, usa la ruta por defecto.
        """
        if dictionary_path is None:
            # Usar ruta por defecto relativa al proyecto
            base_dir = Path(__file__).resolve().parent.parent.parent
            dictionary_path = base_dir / "config" / "table_synonyms.json"

        self.dictionary_path = dictionary_path
        self.dictionary: Dict = {}
        self.table_synonyms: Dict = {}
        self.column_synonyms: Dict = {}
        self.real_table_names: List[str] = []

        # Cache para optimizar búsquedas repetidas
        self._normalization_cache: Dict[str, str] = {}
        self._fuzzy_cache: Dict[str, Optional[str]] = {}

        # Configuración de fuzzy matching
        self.fuzzy_threshold = 0.75  # Umbral de similitud (0.0 a 1.0)
        self.max_fuzzy_distance = 3  # Máxima distancia de edición permitida

        self._load_dictionary()
        self._build_lookup_structures()

    def _load_dictionary(self):
        """Carga el diccionario de sinónimos desde el archivo JSON."""
        try:
            if not os.path.exists(self.dictionary_path):
                logger.warning(f"Dictionary file not found at {self.dictionary_path}")
                logger.warning("Text normalization will be limited")
                return

            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                self.dictionary = json.load(f)

            self.table_synonyms = self.dictionary.get("table_synonyms", {})
            self.column_synonyms = self.dictionary.get("column_synonyms", {})
            self.real_table_names = list(self.table_synonyms.keys())

            logger.info(f"Loaded dictionary with {len(self.table_synonyms)} tables")
            logger.info(f"Dictionary version: {self.dictionary.get('metadata', {}).get('version', 'unknown')}")

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON dictionary: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading dictionary: {e}")
            raise

    def _build_lookup_structures(self):
        """
        Construye estructuras de búsqueda optimizadas para acceso rápido.
        Crea un mapa inverso: sinónimo -> nombre_real_tabla
        """
        self._synonym_to_table: Dict[str, str] = {}
        self._column_synonym_to_real: Dict[str, str] = {}

        # Mapear todos los sinónimos de tablas a sus nombres reales
        for real_table, config in self.table_synonyms.items():
            # Agregar variaciones singulares
            for singular in config.get("singular", []):
                self._synonym_to_table[singular.lower()] = real_table

            # Agregar sinónimos
            for synonym in config.get("synonyms", []):
                self._synonym_to_table[synonym.lower()] = real_table

            # Agregar errores comunes
            for error in config.get("common_errors", []):
                self._synonym_to_table[error.lower()] = real_table

            # Agregar el nombre real mismo
            self._synonym_to_table[real_table.lower()] = real_table

        # Mapear sinónimos de columnas
        for real_column, synonyms in self.column_synonyms.items():
            for synonym in synonyms:
                self._column_synonym_to_real[synonym.lower()] = real_column
            self._column_synonym_to_real[real_column.lower()] = real_column

        logger.info(f"Built lookup structures: {len(self._synonym_to_table)} table mappings, "
                   f"{len(self._column_synonym_to_real)} column mappings")

    def normalize_query(self, user_query: str, enable_fuzzy: bool = True) -> str:
        """
        Normaliza una consulta completa del usuario.

        Args:
            user_query: Consulta en lenguaje natural del usuario
            enable_fuzzy: Si True, aplica fuzzy matching para palabras no encontradas

        Returns:
            Consulta normalizada con nombres de tablas/columnas correctos
        """
        if not user_query:
            return user_query

        # Verificar cache
        cache_key = f"{user_query}:{enable_fuzzy}"
        if cache_key in self._normalization_cache:
            logger.debug("Returning cached normalization")
            return self._normalization_cache[cache_key]

        logger.debug(f"Normalizing query: {user_query[:100]}...")

        normalized = user_query
        replacements_made = 0

        # Paso 1: Normalizar nombres de tablas usando el diccionario
        for synonym, real_table in self._synonym_to_table.items():
            # Usar word boundaries para evitar reemplazos parciales
            pattern = r'\b' + re.escape(synonym) + r'\b'
            matches = re.findall(pattern, normalized, re.IGNORECASE)

            if matches:
                normalized = re.sub(pattern, real_table, normalized, flags=re.IGNORECASE)
                replacements_made += len(matches)
                logger.debug(f"Replaced '{synonym}' -> '{real_table}' ({len(matches)} times)")

        # Paso 2: Si fuzzy matching está habilitado, buscar palabras similares
        if enable_fuzzy:
            fuzzy_replacements = self._apply_fuzzy_matching(normalized)
            if fuzzy_replacements:
                for original, replacement in fuzzy_replacements:
                    pattern = r'\b' + re.escape(original) + r'\b'
                    normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
                    replacements_made += 1
                    logger.debug(f"Fuzzy replaced '{original}' -> '{replacement}'")

        # Guardar en cache
        self._normalization_cache[cache_key] = normalized

        # Limpiar cache si crece mucho (más de 1000 entradas)
        if len(self._normalization_cache) > 1000:
            self._normalization_cache.clear()
            logger.debug("Cleared normalization cache")

        logger.info(f"Normalization complete: {replacements_made} replacements made")
        return normalized

    def _apply_fuzzy_matching(self, text: str) -> List[Tuple[str, str]]:
        """
        Aplica fuzzy matching para encontrar palabras similares a nombres de tablas.

        Args:
            text: Texto a analizar

        Returns:
            Lista de tuplas (palabra_original, nombre_tabla_real)
        """
        replacements = []
        words = self._extract_words(text)

        for word in words:
            word_lower = word.lower()

            # Verificar si ya está en el diccionario
            if word_lower in self._synonym_to_table:
                continue

            # Verificar cache de fuzzy
            if word_lower in self._fuzzy_cache:
                match = self._fuzzy_cache[word_lower]
                if match:
                    replacements.append((word, match))
                continue

            # Buscar tabla similar
            best_match = self._find_similar_table(word_lower)

            # Guardar en cache
            self._fuzzy_cache[word_lower] = best_match

            if best_match:
                replacements.append((word, best_match))
                logger.debug(f"Fuzzy match found: '{word}' ~= '{best_match}'")

        return replacements

    def _find_similar_table(self, word: str) -> Optional[str]:
        """
        Encuentra la tabla más similar a una palabra usando fuzzy matching.

        Args:
            word: Palabra a buscar

        Returns:
            Nombre de la tabla más similar o None si no hay coincidencia
        """
        if len(word) < 3:  # Ignorar palabras muy cortas
            return None

        best_match = None
        best_ratio = 0.0
        best_distance = float('inf')

        for table_name in self.real_table_names:
            # Calcular similitud usando SequenceMatcher
            ratio = SequenceMatcher(None, word, table_name.lower()).ratio()

            # Calcular distancia de Levenshtein simple
            distance = self._levenshtein_distance(word, table_name.lower())

            # Actualizar mejor coincidencia si supera el umbral
            if ratio > best_ratio and ratio >= self.fuzzy_threshold and distance <= self.max_fuzzy_distance:
                best_ratio = ratio
                best_distance = distance
                best_match = table_name

        if best_match:
            logger.debug(f"Fuzzy match: '{word}' -> '{best_match}' "
                        f"(similarity: {best_ratio:.2f}, distance: {best_distance})")

        return best_match

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calcula la distancia de Levenshtein entre dos cadenas.

        Args:
            s1: Primera cadena
            s2: Segunda cadena

        Returns:
            Distancia de edición (número mínimo de operaciones)
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Costo de inserción, eliminación o sustitución
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _extract_words(self, text: str) -> Set[str]:
        """
        Extrae palabras individuales del texto, filtrando palabras comunes.

        Args:
            text: Texto a procesar

        Returns:
            Conjunto de palabras extraídas
        """
        # Palabras a ignorar (stop words comunes en español)
        stop_words = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'en', 'a', 'por', 'para', 'con', 'sin',
            'que', 'y', 'o', 'pero', 'si', 'no', 'me', 'te', 'se',
            'dame', 'dame', 'muestra', 'muestrame', 'lista', 'listar',
            'cuanto', 'cuantos', 'cuanta', 'cuantas', 'cual', 'cuales',
            'hay', 'tiene', 'tienen', 'esta', 'estan', 'todo', 'todos',
            'toda', 'todas', 'tengo', 'tenemos', 'donde', 'cuando'
        }

        # Extraer palabras (letras, números y guiones bajos)
        words = re.findall(r'\b[a-záéíóúñ_]+\b', text.lower())

        # Filtrar stop words y palabras muy cortas
        filtered_words = {
            word for word in words
            if word not in stop_words and len(word) >= 3
        }

        return filtered_words

    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """
        Obtiene información sobre una tabla del diccionario.

        Args:
            table_name: Nombre de la tabla

        Returns:
            Diccionario con información de la tabla o None
        """
        return self.table_synonyms.get(table_name.lower())

    def get_all_table_names(self) -> List[str]:
        """
        Obtiene la lista de todos los nombres reales de tablas.

        Returns:
            Lista de nombres de tablas
        """
        return self.real_table_names.copy()

    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas sobre el normalizador.

        Returns:
            Diccionario con estadísticas
        """
        total_synonyms = sum(
            len(config.get("singular", [])) +
            len(config.get("synonyms", [])) +
            len(config.get("common_errors", []))
            for config in self.table_synonyms.values()
        )

        return {
            "total_tables": len(self.real_table_names),
            "total_table_synonyms": len(self._synonym_to_table),
            "total_column_synonyms": len(self._column_synonym_to_real),
            "cache_size": len(self._normalization_cache),
            "fuzzy_cache_size": len(self._fuzzy_cache),
            "fuzzy_threshold": self.fuzzy_threshold,
            "max_fuzzy_distance": self.max_fuzzy_distance,
            "dictionary_version": self.dictionary.get("metadata", {}).get("version", "unknown")
        }

    def clear_cache(self):
        """Limpia los caches de normalización."""
        self._normalization_cache.clear()
        self._fuzzy_cache.clear()
        logger.info("Caches cleared")


# Instancia singleton para uso global
_normalizer_instance: Optional[TextNormalizer] = None


def get_text_normalizer() -> TextNormalizer:
    """
    Obtiene la instancia singleton del normalizador de texto.

    Returns:
        Instancia de TextNormalizer
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = TextNormalizer()
        logger.info("TextNormalizer singleton instance created")
    return _normalizer_instance
