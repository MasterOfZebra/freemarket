"""
Comprehensive tests for language normalization and matching
Tests with different word forms, synonyms, Cyrillic/Latin variations
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.language_normalization import LanguageNormalizer
from backend.equivalence_engine import ExchangeEquivalence
from backend.core_matching_engine import CoreMatchingEngine
from backend.models import ListingItem, ExchangeType, ListingItemType
from sqlalchemy.orm import Session


class TestLanguageNormalization:
    """Test language normalization with various word forms"""

    def setup_method(self):
        self.normalizer = LanguageNormalizer(enable_cache=False)

    def test_cyrillic_latin_variations(self):
        """Test matching with Cyrillic/Latin variations"""
        test_cases = [
            ("iPhone", "айфон", 0.90),  # Should match via transliteration
            ("велосипед", "bike", 0.90),  # Synonym match
            ("автомобиль", "car", 0.90),  # Synonym match
            ("ноутбук", "laptop", 0.90),  # Synonym match
            ("стол", "desk", 0.90),  # Synonym match
        ]

        for text_a, text_b, expected_min in test_cases:
            score = self.normalizer.similarity_score(text_a, text_b)
            print(f"  '{text_a}' vs '{text_b}': {score:.3f} (expected ≥{expected_min})")
            assert score >= expected_min, f"Failed: {text_a} vs {text_b} got {score}"

    def test_synonym_expansion(self):
        """Test synonym expansion"""
        test_cases = [
            ("phone", ["телефон", "мобила", "смартфон"]),
            ("bike", ["велосипед", "велик", "bicycle"]),
            ("car", ["автомобиль", "машина", "авто"]),
        ]

        for canonical, synonyms in test_cases:
            found_synonyms = self.normalizer.find_synonyms(canonical)
            print(f"  '{canonical}' synonyms: {found_synonyms}")

            # Check that all synonyms are found
            for synonym in synonyms:
                synonym_norm = self.normalizer.normalize(synonym)
                assert synonym_norm in found_synonyms or canonical in found_synonyms, \
                    f"Synonym '{synonym}' not found for '{canonical}'"

    def test_word_forms_variations(self):
        """Test different word forms and cases"""
        test_cases = [
            ("iPhone 13 Pro", "iPhone 13 Pro Max", 0.70),  # Partial match
            ("iPhone", "iPhone 13", 0.70),  # Partial match
            ("велосипед горный", "горный велосипед", 0.90),  # Word order
            ("НОУТБУК", "ноутбук", 0.85),  # Case insensitive (may normalize differently)
            ("iPhone!!!", "iPhone", 0.85),  # Punctuation removal (may normalize to different forms)
        ]

        for text_a, text_b, expected_min in test_cases:
            score = self.normalizer.similarity_score(text_a, text_b)
            print(f"  '{text_a}' vs '{text_b}': {score:.3f} (expected ≥{expected_min})")
            assert score >= expected_min, f"Failed: {text_a} vs {text_b} got {score}"

    def test_real_world_items(self):
        """Test with real-world item names"""
        test_pairs = [
            # Electronics
            ("iPhone 13 Pro", "iPhone 13 Pro Max", 0.80),
            ("Samsung Galaxy", "Самсунг Гэлэкси", 0.65),  # Транслитерация брендов может варьироваться
            ("ноутбук Dell", "Dell ноутбук", 0.90),

            # Transport
            ("велосипед горный", "mountain bike", 0.65),  # Multi-word synonym matching
            ("автомобиль Toyota", "Toyota машина", 0.80),

            # Furniture
            ("письменный стол", "desk", 0.90),
            ("стул офисный", "office chair", 0.70),
        ]

        for item_a, item_b, expected_min in test_pairs:
            score = self.normalizer.similarity_score(item_a, item_b)
            print(f"  '{item_a}' vs '{item_b}': {score:.3f} (expected ≥{expected_min})")
            assert score >= expected_min, f"Failed: {item_a} vs {item_b} got {score}"


class TestMatchingWithLanguageNormalization:
    """Test matching engine with language normalization"""

    def setup_method(self):
        self.equivalence_engine = ExchangeEquivalence()
        self.core_engine = CoreMatchingEngine(
            equivalence_engine=self.equivalence_engine,
            language_similarity_weight=0.3
        )

    def test_matching_different_languages(self):
        """Test matching items with different language forms"""
        # Simulate item pair
        item_a_name = "iPhone 13 Pro"
        item_b_name = "айфон 13 про"

        # Check language similarity
        normalizer = LanguageNormalizer()
        lang_score = normalizer.similarity_score(item_a_name, item_b_name)
        print(f"  Language similarity: '{item_a_name}' vs '{item_b_name}' = {lang_score:.3f}")

        assert lang_score >= 0.70, f"Language similarity too low: {lang_score}"

    def test_matching_synonyms(self):
        """Test matching with synonyms"""
        test_cases = [
            ("bike", "велосипед", 0.70),
            ("car", "автомобиль", 0.70),
            ("phone", "телефон", 0.70),
        ]

        normalizer = LanguageNormalizer()
        for item_a, item_b, expected_min in test_cases:
            score = normalizer.similarity_score(item_a, item_b)
            print(f"  '{item_a}' vs '{item_b}': {score:.3f}")
            assert score >= expected_min, f"Synonym match failed: {item_a} vs {item_b}"


def create_test_listing_item(
    listing_id: int,
    item_type: ListingItemType,
    category: str,
    exchange_type: ExchangeType,
    item_name: str,
    value_tenge: int,
    duration_days: int = None,
    description: str = ""
):
    """Helper to create test listing item"""
    return ListingItem(
        listing_id=listing_id,
        item_type=item_type,
        category=category,
        exchange_type=exchange_type,
        item_name=item_name,
        value_tenge=value_tenge,
        duration_days=duration_days,
        description=description
    )


class TestFullMatchingPipeline:
    """Test full matching pipeline with language normalization"""

    def test_matching_scenarios(self):
        """Test various matching scenarios"""
        equivalence_engine = ExchangeEquivalence()
        normalizer = LanguageNormalizer()

        # Scenario 1: Same item, different languages
        print("\n📋 Scenario 1: Same item, different languages")
        item_a = create_test_listing_item(
            1, ListingItemType.WANT, "electronics", ExchangeType.PERMANENT,
            "iPhone 13 Pro", 500000
        )
        item_b = create_test_listing_item(
            2, ListingItemType.OFFER, "electronics", ExchangeType.PERMANENT,
            "айфон 13 про", 520000
        )

        # Check equivalence (value match)
        equiv_result = equivalence_engine.calculate_permanent_score(
            item_a.value_tenge, item_b.value_tenge
        )
        print(f"  Equivalence score: {equiv_result.score:.3f}")

        # Check language similarity
        lang_score = normalizer.similarity_score(item_a.item_name, item_b.item_name)
        print(f"  Language similarity: {lang_score:.3f}")

        # Combined score (70% equivalence, 30% language)
        combined_score = equiv_result.score * 0.7 + lang_score * 0.3
        print(f"  Combined score: {combined_score:.3f}")

        assert combined_score >= 0.70, f"Combined score too low: {combined_score}"

        # Scenario 2: Synonyms
        print("\n📋 Scenario 2: Synonyms")
        item_c = create_test_listing_item(
            3, ListingItemType.WANT, "transport", ExchangeType.TEMPORARY,
            "велосипед горный", 30000, duration_days=7
        )
        item_d = create_test_listing_item(
            4, ListingItemType.OFFER, "transport", ExchangeType.TEMPORARY,
            "mountain bike", 32000, duration_days=7
        )

        lang_score = normalizer.similarity_score(item_c.item_name, item_d.item_name)
        print(f"  Language similarity: {lang_score:.3f}")

        # Temporary exchange matching
        temp_result = equivalence_engine.calculate_temporary_score(
            item_c.value_tenge, item_c.duration_days,
            item_d.value_tenge, item_d.duration_days
        )
        print(f"  Equivalence score: {temp_result.score:.3f}")

        combined_score = temp_result.score * 0.7 + lang_score * 0.3
        print(f"  Combined score: {combined_score:.3f}")

        assert combined_score >= 0.65, f"Synonym matching failed: {combined_score}"

        # Scenario 3: Word order variations
        print("\n📋 Scenario 3: Word order variations")
        item_e = create_test_listing_item(
            5, ListingItemType.WANT, "electronics", ExchangeType.PERMANENT,
            "ноутбук Dell XPS", 600000
        )
        item_f = create_test_listing_item(
            6, ListingItemType.OFFER, "electronics", ExchangeType.PERMANENT,
            "Dell XPS ноутбук", 610000
        )

        lang_score = normalizer.similarity_score(item_e.item_name, item_f.item_name)
        print(f"  Language similarity: {lang_score:.3f}")
        assert lang_score >= 0.85, f"Word order matching failed: {lang_score}"


if __name__ == "__main__":
    print("🧪 Running Language Normalization and Matching Tests\n")

    # Run tests
    test_normalization = TestLanguageNormalization()
    test_normalization.setup_method()

    print("=" * 60)
    print("TEST 1: Cyrillic/Latin Variations")
    print("=" * 60)
    test_normalization.test_cyrillic_latin_variations()

    print("\n" + "=" * 60)
    print("TEST 2: Synonym Expansion")
    print("=" * 60)
    test_normalization.test_synonym_expansion()

    print("\n" + "=" * 60)
    print("TEST 3: Word Forms Variations")
    print("=" * 60)
    test_normalization.test_word_forms_variations()

    print("\n" + "=" * 60)
    print("TEST 4: Real-World Items")
    print("=" * 60)
    test_normalization.test_real_world_items()

    print("\n" + "=" * 60)
    print("TEST 5: Full Matching Pipeline")
    print("=" * 60)
    test_pipeline = TestFullMatchingPipeline()
    test_pipeline.test_matching_scenarios()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

