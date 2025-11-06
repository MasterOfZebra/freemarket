"""
Комплексное тестирование системы подбора обменов
Проверяет понимание смысла запросов, синонимы, грамматические вариации
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.language_normalization import get_normalizer
    from backend.equivalence_engine import ExchangeEquivalence
    from backend.models import ListingItem, ExchangeType, ListingItemType
except ImportError:
    # Fallback for direct execution
    from language_normalization import get_normalizer
    from equivalence_engine import ExchangeEquivalence
    from models import ListingItem, ExchangeType, ListingItemType


def create_test_item(item_name, category, exchange_type, value_tenge, duration_days=None):
    """Создать тестовый ListingItem"""
    return ListingItem(
        listing_id=1,  # dummy
        item_type=ListingItemType.WANT,  # dummy
        category=category,
        exchange_type=ExchangeType.PERMANENT if exchange_type == "permanent" else ExchangeType.TEMPORARY,
        item_name=item_name,
        value_tenge=value_tenge,
        duration_days=duration_days,
        description=""
    )


class MatchingComprehensionTester:
    """Тестер системы понимания намерений пользователей"""

    def __init__(self):
        self.normalizer = get_normalizer()
        self.equivalence_engine = ExchangeEquivalence()

    def test_semantic_accuracy(self):
        """1.1 Семантическая точность"""
        print("\n" + "="*80)
        print("🎯 1.1 СЕМАНТИЧЕСКАЯ ТОЧНОСТЬ")
        print("="*80)

        test_cases = [
            # Положительные случаи (должны найтись)
            ("велосипед", "байк", "transport", "temporary", 30000, 30000, 7, 7, "✅ ДОЛЖЕН НАЙТИ: синонимы"),
            ("ноутбук Apple", "MacBook", "electronics", "permanent", 600000, 600000, None, None, "✅ ДОЛЖЕН НАЙТИ: бренд синоним"),
            ("ремонт телефона", "починка смартфона", "services", "temporary", 5000, 5000, 1, 1, "✅ ДОЛЖЕН НАЙТИ: смысловые синонимы"),

            # Отрицательные случаи (НЕ должны найтись)
            ("ремонт телефона", "продажа телефона", "services", "temporary", 5000, 500000, 1, None, "❌ НЕ ДОЛЖЕН НАЙТИ: разные намерения"),
            ("прокат велосипеда", "покупка велосипеда", "transport", "temporary", 1000, 50000, 7, None, "❌ НЕ ДОЛЖЕН НАЙТИ: аренда vs покупка"),
        ]

        results = []
        for want_text, offer_text, category, ex_type, want_price, offer_price, want_days, offer_days, expected in test_cases:
            print(f"\n📋 Тест: '{want_text}' ↔ '{offer_text}'")

            # Создаем тестовые items
            want_item = create_test_item(want_text, category, ex_type, want_price, want_days)
            offer_item = create_test_item(offer_text, category, ex_type, offer_price, offer_days)

            # Проверяем language similarity
            lang_score = self.normalizer.similarity_score(want_text, offer_text)
            print(f"  Language similarity: {lang_score:.3f}")

            # Проверяем equivalence
            if ex_type == "permanent":
                equiv_result = self.equivalence_engine.calculate_permanent_score(want_price, offer_price)
            else:
                equiv_result = self.equivalence_engine.calculate_temporary_score(
                    want_price, want_days or 1, offer_price, offer_days or 1
                )

            print(f"  Equivalence score: {equiv_result.score:.3f} ({equiv_result.category.value})")

            # Combined score (70% equivalence + 30% language)
            combined_score = equiv_result.score * 0.7 + lang_score * 0.3
            print(f"  Combined score: {combined_score:.3f}")

            # Оценка результата
            is_match = equiv_result.is_match and combined_score >= 0.70
            should_match = "✅ ДОЛЖЕН" in expected

            if should_match and is_match:
                status = "✅ PASS"
            elif not should_match and not is_match:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"

            print(f"  Result: {status} | Expected: {expected}")
            print(f"  Match: {is_match} | Combined: {combined_score:.3f}")

            results.append({
                'test': f"{want_text} ↔ {offer_text}",
                'lang_score': lang_score,
                'equiv_score': equiv_result.score,
                'combined_score': combined_score,
                'is_match': is_match,
                'expected_match': should_match,
                'status': status
            })

        # Итоги
        passed = sum(1 for r in results if r['status'] == "✅ PASS")
        total = len(results)
        print(f"\n📊 Результаты семантической точности: {passed}/{total} ({passed/total*100:.1f}%)")

        return results

    def test_grammar_orthography(self):
        """1.2 Грамматические вариации и орфография"""
        print("\n" + "="*80)
        print("📝 1.2 ГРАММАТИЧЕСКИЕ ВАРИАЦИИ И ОРФОГРАФИЯ")
        print("="*80)

        test_cases = [
            # Грамматические вариации (должны найтись)
            ("игровая приставка", "игровые приставки", "electronics", "permanent", 50000, 50000, "✅ ДОЛЖЕН НАЙТИ: формы числа"),
            ("велосепед", "велосипед", "transport", "temporary", 30000, 30000, 7, 7, "✅ ДОЛЖЕН НАЙТИ: опечатка"),
            ("сдать квартиру", "сдаю квартиру", "housing", "temporary", 15000, 15000, 30, 30, "✅ ДОЛЖЕН НАЙТИ: формы глагола"),

            # Разные намерения (НЕ должны найтись)
            ("сдать квартиру", "снять квартиру", "housing", "temporary", 15000, 15000, 30, 30, "❌ НЕ ДОЛЖЕН НАЙТИ: разные намерения"),
        ]

        results = []
        for text1, text2, category, ex_type, price1, price2, days1, days2, expected in test_cases:
            print(f"\n📋 Тест: '{text1}' ↔ '{text2}'")

            lang_score = self.normalizer.similarity_score(text1, text2)
            print(f"  Language similarity: {lang_score:.3f}")

            # Для грамматических тестов используем permanent (упрощаем)
            equiv_result = self.equivalence_engine.calculate_permanent_score(price1, price2)
            combined_score = equiv_result.score * 0.7 + lang_score * 0.3

            is_match = equiv_result.is_match and combined_score >= 0.70
            should_match = "✅ ДОЛЖЕН" in expected

            if should_match and is_match:
                status = "✅ PASS"
            elif not should_match and not is_match:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"

            print(f"  Result: {status} | Expected: {expected}")
            print(f"  Combined score: {combined_score:.3f}")

            results.append({
                'test': f"{text1} ↔ {text2}",
                'lang_score': lang_score,
                'combined_score': combined_score,
                'is_match': is_match,
                'expected_match': should_match,
                'status': status
            })

        passed = sum(1 for r in results if r['status'] == "✅ PASS")
        total = len(results)
        print(f"\n📊 Результаты грамматики/орфографии: {passed}/{total} ({passed/total*100:.1f}%)")

        return results

    def test_category_compatibility(self):
        """1.3 Категориальная совместимость (межкатегорийный обмен)"""
        print("\n" + "="*80)
        print("🔄 1.3 КАТЕГОРИАЛЬНАЯ СОВМЕСТИМОСТЬ")
        print("="*80)

        # Межкатегорийные тесты - разные категории, но один тип обмена
        test_cases = [
            ("гитара", "курсы английского", "music", "education", "temporary", 25000, 15000, 10, 20, "✅ ДОЛЖЕН НАЙТИ: разные категории, но услуги"),
            ("квартира на сутки", "аренда авто", "housing", "transport", "temporary", 20000, 8000, 1, 1, "✅ ДОЛЖЕН НАЙТИ: аренда ↔ аренда"),
            ("работа программиста", "услуги дизайнера", "services", "services", "temporary", 50000, 30000, 30, 15, "✅ ДОЛЖЕН НАЙТИ: услуги ↔ услуги"),
        ]

        results = []
        for want_text, offer_text, want_cat, offer_cat, ex_type, want_price, offer_price, want_days, offer_days, expected in test_cases:
            print(f"\n📋 Тест: '{want_text}' ({want_cat}) ↔ '{offer_text}' ({offer_cat})")

            # Проверяем language similarity
            lang_score = self.normalizer.similarity_score(want_text, offer_text)
            print(f"  Language similarity: {lang_score:.3f}")

            # Проверяем equivalence (temporary exchange)
            equiv_result = self.equivalence_engine.calculate_temporary_score(
                want_price, want_days, offer_price, offer_days
            )

            combined_score = equiv_result.score * 0.7 + lang_score * 0.3

            print(f"  Equivalence score: {equiv_result.score:.3f}")
            print(f"  Combined score: {combined_score:.3f}")

            # В межкатегорийном обмене логика та же - проверяем совпадение
            is_match = equiv_result.is_match and combined_score >= 0.70

            # Для межкатегорийных обменов оцениваем по смыслу
            should_match = "✅ ДОЛЖЕН" in expected

            if should_match and is_match:
                status = "✅ PASS"
            elif not should_match and not is_match:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"

            print(f"  Result: {status} | Expected: {expected}")

            results.append({
                'test': f"{want_text} ({want_cat}) ↔ {offer_text} ({offer_cat})",
                'lang_score': lang_score,
                'equiv_score': equiv_result.score,
                'combined_score': combined_score,
                'is_match': is_match,
                'expected_match': should_match,
                'status': status
            })

        passed = sum(1 for r in results if r['status'] == "✅ PASS")
        total = len(results)
        print(f"\n📊 Результаты категориальной совместимости: {passed}/{total} ({passed/total*100:.1f}%)")

        return results

    def run_all_tests(self):
        """Запустить все тесты"""
        print("🧪 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ ПОДБОРА ОБМЕНОВ")
        print("="*80)

        all_results = []

        # 1. Семантическая точность
        semantic_results = self.test_semantic_accuracy()
        all_results.extend(semantic_results)

        # 2. Грамматика и орфография
        grammar_results = self.test_grammar_orthography()
        all_results.extend(grammar_results)

        # 3. Категориальная совместимость
        category_results = self.test_category_compatibility()
        all_results.extend(category_results)

        # Итоговые результаты
        print("\n" + "="*80)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("="*80)

        total_passed = sum(1 for r in all_results if r['status'] == "✅ PASS")
        total_tests = len(all_results)

        print(f"Общее количество тестов: {total_tests}")
        print(f"Прошло успешно: {total_passed}")
        print(f"Успешность: {total_passed/total_tests*100:.1f}%")

        # Детализация по типам
        semantic_passed = sum(1 for r in semantic_results if r['status'] == "✅ PASS")
        grammar_passed = sum(1 for r in grammar_results if r['status'] == "✅ PASS")
        category_passed = sum(1 for r in category_results if r['status'] == "✅ PASS")

        print("\nПо категориям:")
        print(f"  Семантическая точность: {semantic_passed}/{len(semantic_results)}")
        print(f"  Грамматика/орфография: {grammar_passed}/{len(grammar_results)}")
        print(f"  Категориальная совместимость: {category_passed}/{len(category_results)}")

        return all_results


if __name__ == "__main__":
    tester = MatchingComprehensionTester()
    results = tester.run_all_tests()
