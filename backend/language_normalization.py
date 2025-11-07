"""
Language Normalization Module

Handles:
- Cyrillic ↔ Latin transliteration
- Synonym expansion and mapping
- Text normalization (lowercase, punctuation removal)
- Similarity scoring (cosine, Levenshtein)

Used in matching engine to ensure consistent matching across language variations.
"""

import re
import unicodedata
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from rapidfuzz import fuzz, process  # type: ignore
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


class LanguageNormalizer:
    """Multi-language text normalization for matching"""

    # Cyrillic to Latin transliteration map
    CYRILLIC_TO_LATIN = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch',
        'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
        'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    }

    # Synonym mappings loaded from JSON file
    SYNONYM_MAP: Dict[str, List[str]] = {}

    @classmethod
    def _load_synonyms(cls) -> Dict[str, List[str]]:
        """Load synonyms from JSON file"""
        synonyms_file = Path(__file__).parent / "data" / "synonyms.json"

        try:
            with open(synonyms_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Flatten all synonym groups into single dict
            synonyms = {}
            for category, category_synonyms in data.get('synonyms', {}).items():
                synonyms.update(category_synonyms)

            logger.info(f"Loaded {len(synonyms)} synonym entries from {synonyms_file}")
            return synonyms

        except Exception as e:
            logger.warning(f"Could not load synonyms from {synonyms_file}: {e}")
            # Fallback to minimal synonyms
            return {
                'iphone': ['айфон', 'телефон'],
                'phone': ['телефон', 'айфон'],
                'bike': ['велосипед', 'байк'],
                'guitar': ['гитара'],
                'service': ['услуга', 'работа'],
                'rent': ['аренда', 'прокат'],
            }

    @classmethod
    def _load_stopwords(cls) -> Set[str]:
        """Load stopwords from text file"""
        stopwords_file = Path(__file__).parent / "data" / "stopwords.txt"

        try:
            stopwords = set()
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        stopwords.add(line.lower())

            logger.info(f"Loaded {len(stopwords)} stopwords from {stopwords_file}")
            return stopwords

        except Exception as e:
            logger.warning(f"Could not load stopwords from {stopwords_file}: {e}")
            # Fallback to minimal stopwords
            return {
                'и', 'или', 'но', 'в', 'на', 'из', 'к', 'за', 'с', 'по',
                'от', 'из', 'у', 'не', 'да', 'нет', 'что', 'кто', 'это',
                'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at',
                'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'
            }

    # Stopwords to remove (loaded from file)
    STOPWORDS: Set[str] = set()

    def __init__(self, enable_cache: bool = True, cache_size: int = 10000):
        """
        Initialize normalizer

        Args:
            enable_cache: Enable caching of normalized results
            cache_size: Maximum cache size
        """
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        self._normalize_cache: Dict[str, str] = {}
        self._similarity_cache: Dict[Tuple[str, str], float] = {}

        # Initialize sentence transformer model for semantic similarity
        self.semantic_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("Loaded sentence transformer model for semantic similarity")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer model: {e}")

        # Load synonyms and stopwords from file
        if not self.__class__.SYNONYM_MAP:
            self.__class__.SYNONYM_MAP = self._load_synonyms()

        if not self.__class__.STOPWORDS:
            self.__class__.STOPWORDS = self._load_stopwords()

    def transliterate_cyrillic_to_latin(self, text: str) -> str:
        """Convert Cyrillic text to Latin representation"""
        result = []
        for char in text:
            result.append(self.CYRILLIC_TO_LATIN.get(char, char))
        return ''.join(result)

    def normalize(self, text: str, language: str = 'auto') -> str:
        """
        Full normalization pipeline

        Args:
            text: Raw input text
            language: 'en', 'ru', or 'auto' for auto-detection

        Returns:
            Canonical normalized form
        """
        if not text:
            return ""

        # Check cache
        cache_key = f"{text}_{language}"
        if self.enable_cache and cache_key in self._normalize_cache:
            return self._normalize_cache[cache_key]

        original_text = text

        # 1. Normalize Unicode and case first
        text = text.lower()
        text = unicodedata.normalize('NFKD', text)

        # 2. Transliteration (before removing punctuation)
        if language in ['ru', 'auto']:
            # Try to detect if text contains Cyrillic
            if any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in text):
                text = self.transliterate_cyrillic_to_latin(text)

        # 3. Remove punctuation (keep alphanumeric and spaces)
        text = self._remove_punctuation(text)

        # 4. Convert to ASCII (but keep transliterated letters)
        # Use more lenient approach - keep transliterated results
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = text.strip()

        # 5. Remove stopwords
        words = text.split()
        words = [w for w in words if w and w not in self.STOPWORDS and len(w) > 1]
        result = ' '.join(words)

        # Cache result (use original text as key for consistent caching)
        if self.enable_cache and len(self._normalize_cache) < self.cache_size:
            self._normalize_cache[cache_key] = result

        return result

    def _remove_punctuation(self, text: str) -> str:
        """Remove punctuation from text"""
        # Keep only alphanumeric, space, and Cyrillic characters
        return re.sub(r'[^\w\s\u0400-\u04FF]', ' ', text)

    def find_synonyms(self, text: str) -> List[str]:
        """Find all known synonyms for text"""
        normalized = self.normalize(text)

        results = [normalized]

        # Check if normalized text matches any canonical form
        for canonical, synonyms in self.SYNONYM_MAP.items():
            canonical_norm = self.normalize(canonical)
            if canonical_norm == normalized:
                results.extend([self.normalize(s) for s in synonyms])
                break

            # Also check if it matches any synonym
            for synonym in synonyms:
                synonym_norm = self.normalize(synonym)
                if synonym_norm == normalized:
                    results.append(canonical_norm)
                    results.extend([self.normalize(s) for s in synonyms])
                    break

        # Check for word-level synonyms (for multi-word phrases)
        words = normalized.split()
        if len(words) > 1:
            # Try to find synonyms for each word
            word_synonyms = []
            for word in words:
                word_syn_list = []
                for canonical, synonyms in self.SYNONYM_MAP.items():
                    canonical_norm = self.normalize(canonical)
                    if canonical_norm == word:
                        word_syn_list.extend([self.normalize(s) for s in synonyms])
                    for synonym in synonyms:
                        if self.normalize(synonym) == word:
                            word_syn_list.append(canonical_norm)
                            word_syn_list.extend([self.normalize(s) for s in synonyms])

                if word_syn_list:
                    word_synonyms.append(list(set(word_syn_list)))
                else:
                    word_synonyms.append([word])

            # Generate combinations of synonyms
            if word_synonyms:
                from itertools import product
                for combo in product(*word_synonyms):
                    results.append(' '.join(combo))

        return list(set(filter(None, results)))

    def similarity_score(self, text_a: str, text_b: str) -> float:
        """
        Calculate similarity between two texts

        Strategy (priority order):
        1. Exact match = 1.0
        2. Synonym match = 0.90
        3. Partial word match = 0.85
        4. Levenshtein ratio = variable

        Args:
            text_a: First text
            text_b: Second text

        Returns:
            Similarity score (0.0 - 1.0)
        """
        if not text_a or not text_b:
            return 0.0

        # Check cache
        cache_key = (text_a, text_b)
        if self.enable_cache and cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        a_norm = self.normalize(text_a)
        b_norm = self.normalize(text_b)

        if not a_norm or not b_norm:
            return 0.0

        # Initialize score
        score = 0.0

        # Exact match
        if a_norm == b_norm:
            score = 1.0
        # Synonym match (check both directions and word-level)
        a_synonyms = self.find_synonyms(a_norm)
        b_synonyms = self.find_synonyms(b_norm)

        if b_norm in a_synonyms or a_norm in b_synonyms:
            score = 0.90
        # Check word-level synonym matching for multi-word phrases
        elif len(a_norm.split()) > 1 and len(b_norm.split()) > 1:
            a_words = set(a_norm.split())
            b_words = set(b_norm.split())

            # Check if words are synonyms
            synonym_matches = 0
            total_words = max(len(a_words), len(b_words))

            for a_word in a_words:
                a_word_syns = set(self.find_synonyms(a_word))
                for b_word in b_words:
                    if b_word in a_word_syns or b_word == a_word:
                        synonym_matches += 1
                        break

            if synonym_matches >= total_words * 0.5:  # At least 50% words match as synonyms
                score = 0.75 + (synonym_matches / total_words) * 0.15  # 0.75-0.90 range
        # Check if one contains the other (partial match)
        elif a_norm in b_norm or b_norm in a_norm:
            # If one is a substring of the other, give bonus
            shorter = min(len(a_norm), len(b_norm))
            longer = max(len(a_norm), len(b_norm))
            substring_score = shorter / longer
            score = 0.70 + (substring_score * 0.20)  # 0.70-0.90 range
        # Check word overlap
        else:
            a_words = set(a_norm.split())
            b_words = set(b_norm.split())
            if a_words and b_words:
                overlap = len(a_words & b_words)
                total_unique = len(a_words | b_words)
                word_overlap_score = overlap / total_unique if total_unique > 0 else 0.0

                # If all words match (word order doesn't matter), boost score
                if overlap == len(a_words) == len(b_words) and overlap > 0:
                    score = 0.90  # High score for same words in different order
                elif word_overlap_score >= 0.5:  # At least 50% word overlap
                    # Good overlap - use weighted combination
                    levenshtein_score = SequenceMatcher(None, a_norm, b_norm).ratio()
                    score = max(word_overlap_score * 0.8 + levenshtein_score * 0.2, levenshtein_score)
                    # Ensure minimum threshold for good matches
                    if word_overlap_score >= 0.6:
                        score = max(score, 0.70)
                else:
                    # Combine word overlap with Levenshtein
                    levenshtein_score = SequenceMatcher(None, a_norm, b_norm).ratio()
                    score = max(word_overlap_score * 0.7 + levenshtein_score * 0.3, levenshtein_score)
            else:
                # Fallback to Levenshtein
                score = SequenceMatcher(None, a_norm, b_norm).ratio()

        # Add fuzzy matching boost for typos using rapidfuzz
        if RAPIDFUZZ_AVAILABLE:
            fuzzy_ratio = fuzz.ratio(text_a.lower(), text_b.lower()) / 100.0
            fuzzy_token_sort = fuzz.token_sort_ratio(text_a.lower(), text_b.lower()) / 100.0
            fuzzy_score = (fuzzy_ratio * 0.6 + fuzzy_token_sort * 0.4)

            # Boost score if fuzzy matching is significantly better
            if fuzzy_score > score and fuzzy_score > 0.8:
                score = min(1.0, score * 1.2)  # Boost by 20% but cap at 1.0
        else:
            # rapidfuzz not available, skip fuzzy boost
            pass

        # Add semantic vector similarity (0.4 weight)
        vector_sim = self.vector_similarity(text_a, text_b)

        # Combine lexical score (0.6) with semantic score (0.4)
        final_score = score * 0.6 + vector_sim * 0.4

        # Cache result
        if self.enable_cache and len(self._similarity_cache) < self.cache_size:
            self._similarity_cache[cache_key] = final_score

        return final_score

    def vector_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate semantic similarity using sentence transformers

        Args:
            text_a: First text
            text_b: Second text

        Returns:
            Similarity score (0.0 - 1.0) or 0.0 if model not available
        """
        if not self.semantic_model or not SENTENCE_TRANSFORMERS_AVAILABLE:
            return 0.0

        if not text_a or not text_b:
            return 0.0

        try:
            # Encode texts to vectors
            embeddings = self.semantic_model.encode([text_a, text_b])
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            return max(0.0, min(1.0, similarity))  # Clamp to [0,1]
        except Exception as e:
            logger.warning(f"Error calculating vector similarity: {e}")
            return 0.0

    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        normalized = self.normalize(text)
        if not normalized:
            return []

        words = normalized.split()
        # Filter by minimum length and not stopwords
        return [w for w in words if len(w) > 2]

    def calculate_text_similarity_matrix(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Calculate similarity matrix for a list of texts

        Returns:
            Matrix[i][j] = similarity(texts[i], texts[j])
        """
        n = len(texts)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i, n):
                score = self.similarity_score(texts[i], texts[j])
                matrix[i][j] = score
                matrix[j][i] = score

        return matrix

    def clear_cache(self):
        """Clear normalization and similarity caches"""
        self._normalize_cache.clear()
        self._similarity_cache.clear()
        logger.info("Language normalizer caches cleared")


# Global instance for singleton usage
_normalizer_instance: Optional[LanguageNormalizer] = None


def get_normalizer() -> LanguageNormalizer:
    """Get or create global normalizer instance"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = LanguageNormalizer()
    return _normalizer_instance


if __name__ == "__main__":
    # Test the normalizer
    normalizer = LanguageNormalizer()

    print("🧪 Language Normalizer Tests\n")

    # Test 1: Transliteration
    print("✅ TEST 1: Transliteration")
    print(f"  айфон → {normalizer.transliterate_cyrillic_to_latin('айфон')}")
    print(f"  велосипед → {normalizer.transliterate_cyrillic_to_latin('велосипед')}")

    # Test 2: Normalization
    print("\n✅ TEST 2: Normalization")
    print(f"  'iPhone' → '{normalizer.normalize('iPhone')}'")
    print(f"  'ВЕЛИК!!!' → '{normalizer.normalize('ВЕЛИК!!!')}'")
    print(f"  'айфон' → '{normalizer.normalize('айфон')}'")

    # Test 3: Synonyms
    print("\n✅ TEST 3: Synonyms")
    print(f"  Synonyms of 'bike': {normalizer.find_synonyms('bike')}")
    print(f"  Synonyms of 'велосипед': {normalizer.find_synonyms('велосипед')}")

    # Test 4: Similarity
    print("\n✅ TEST 4: Similarity Scores")
    print(f"  'iPhone' vs 'айфон': {normalizer.similarity_score('iPhone', 'айфон'):.2f}")
    print(f"  'bike' vs 'велосипед': {normalizer.similarity_score('bike', 'велосипед'):.2f}")
    print(f"  'phone' vs 'bicycle': {normalizer.similarity_score('phone', 'bicycle'):.2f}")

    # Test 5: Keywords
    print("\n✅ TEST 5: Keywords Extraction")
    print(f"  Keywords in 'Used iPhone in good condition': {normalizer.extract_keywords('Used iPhone in good condition')}")
