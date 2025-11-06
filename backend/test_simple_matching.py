"""
Простой тест системы понимания намерений пользователей
Тестирует language normalization без сложных зависимостей
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from language_normalization import LanguageNormalizer, get_normalizer
from equivalence_engine import ExchangeEquivalence


class SimpleMatchingTester:
    """Простой тестер системы понимания намерений"""

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
            ("велосипед", "байк", 30000, 30000, "transport", "temporary", 7, 7, "✅ ДОЛЖЕН НАЙТИ: синонимы"),
            ("iPhone", "айфон", 500000, 500000, "electronics", "permanent", None, None, "✅ ДОЛЖЕН НАЙТИ: транслитерация"),
            ("ноутбук", "laptop", 400000, 400000, "electronics", "permanent", None, None, "✅ ДОЛЖЕН НАЙТИ: синонимы"),

            # Отрицательные случаи (НЕ должны найтись)
            ("ремонт телефона", "продажа телефона", 5000, 500000, "services", "temporary", 1, None, "❌ НЕ ДОЛЖЕН НАЙТИ: разные намерения"),
            ("прокат велосипеда", "покупка велосипеда", 1000, 50000, "transport", "temporary", 7, None, "❌ НЕ ДОЛЖЕН НАЙТИ: аренда vs покупка"),
        ]

        results = []
        for want_text, offer_text, want_price, offer_price, category, ex_type, want_days, offer_days, expected in test_cases:
            print(f"\n📋 Тест: '{want_text}' ↔ '{offer_text}'")

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
            ("игровая приставка", "игровые приставки", 50000, 50000, "✅ ДОЛЖЕН НАЙТИ: формы числа"),
            ("велосепед", "велосипед", 30000, 30000, "✅ ДОЛЖЕН НАЙТИ: опечатка"),
            ("сдать квартиру", "сдаю квартиру", 15000, 15000, "✅ ДОЛЖЕН НАЙТИ: формы глагола"),

            # Разные намерения (НЕ должны найтись)
            ("сдать квартиру", "снять квартиру", 15000, 15000, "❌ НЕ ДОЛЖЕН НАЙТИ: разные намерения"),
        ]

        results = []
        for text1, text2, price1, price2, expected in test_cases:
            print(f"\n📋 Тест: '{text1}' ↔ '{text2}'")

            lang_score = self.normalizer.similarity_score(text1, text2)
            print(f"  Language similarity: {lang_score:.3f}")

            # Для грамматических тестов используем permanent (упрощаем)
            equiv_result = self.equivalence_engine.calculate_permanent_score(price1, price2)
            combined_score = equiv_result.score * 0.7 + lang_score * 0.3

            # Use same logic as in matching engine
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
        """1.3 Категориальная совместимость"""
        print("\n" + "="*80)
        print("🔄 1.3 КАТЕГОРИАЛЬНАЯ СОВМЕСТИМОСТЬ")
        print("="*80)

        test_cases = [
            # Межкатегорийные тесты (теперь должны проходить с новыми порогами)
            ("гитара", "курсы английского", 25000, 15000, "temporary", 10, 20, "✅ ДОЛЖЕН НАЙТИ: разные категории, услуги (сниженный порог)"),
            ("квартира на сутки", "аренда авто", 20000, 8000, "temporary", 1, 1, "✅ ДОЛЖЕН НАЙТИ: аренда ↔ аренда (синонимы)"),
            ("работа программиста", "услуги дизайнера", 50000, 30000, "temporary", 30, 15, "✅ ДОЛЖЕН НАЙТИ: услуги ↔ услуги (синонимы)"),
        ]

        results = []
        for want_text, offer_text, want_price, offer_price, ex_type, want_days, offer_days, expected in test_cases:
            print(f"\n📋 Тест: '{want_text}' ↔ '{offer_text}'")

            # Проверяем language similarity
            lang_score = self.normalizer.similarity_score(want_text, offer_text)
            print(f"  Language similarity: {lang_score:.3f}")

            # Проверяем equivalence with cross-category tolerance
            is_cross_category = True  # All these tests are cross-category by design
            equiv_result = self.equivalence_engine.calculate_temporary_score(
                want_price, want_days, offer_price, offer_days,
                tolerance=0.5 if is_cross_category else None
            )

            combined_score = equiv_result.score * 0.7 + lang_score * 0.3

            print(f"  Equivalence score: {equiv_result.score:.3f}")
            print(f"  Combined score: {combined_score:.3f}")

            # Use dynamic thresholds like in matching engine
            equivalence_threshold = 0.30 if is_cross_category else self.equivalence_engine.config.MIN_MATCH_SCORE
            threshold = 0.20 if is_cross_category else 0.70
            result_is_match = equiv_result.score >= equivalence_threshold

            is_match = result_is_match and combined_score >= threshold
            should_match = "✅ ДОЛЖЕН" in expected

            if should_match and is_match:
                status = "✅ PASS"
            elif not should_match and not is_match:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"

            print(f"  Result: {status} | Expected: {expected}")

            results.append({
                'test': f"{want_text} ↔ {offer_text}",
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

    def test_false_positives(self):
        """1.8 Отсечение ложных совпадений"""
        print("\n" + "="*80)
        print("🚫 1.8 ОТСЕЧЕНИЕ ЛОЖНЫХ СОВПАДЕНИЙ")
        print("="*80)

        test_cases = [
            # Ложные совпадения (НЕ должны найтись)
            ("курсы дизайна", "работа дизайнером", 20000, 50000, "❌ НЕ ДОЛЖЕН НАЙТИ: разные контексты"),
            ("продажа авто", "аренда авто", 1000000, 15000, "❌ НЕ ДОЛЖЕН НАЙТИ: продажа vs аренда"),
            ("снять жильё", "сдаю жильё", 25000, 25000, "✅ ДОЛЖЕН НАЙТИ: симметричные намерения"),
        ]

        results = []
        for text1, text2, price1, price2, expected in test_cases:
            print(f"\n📋 Тест: '{text1}' ↔ '{text2}'")

            lang_score = self.normalizer.similarity_score(text1, text2)
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

            print(f"  Language: {lang_score:.3f} | Combined: {combined_score:.3f}")
            print(f"  Result: {status} | Expected: {expected}")

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
        print(f"\n📊 Результаты отсечения ложных совпадений: {passed}/{total} ({passed/total*100:.1f}%)")

        return results

    def run_all_tests(self):
        """Запустить все тесты"""
        print("🧪 ЗАПУСК ТЕСТИРОВАНИЯ СИСТЕМЫ ПОНИМАНИЯ НАМЕРЕНИЙ")
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

        # 4. Отсечение ложных совпадений
        false_positive_results = self.test_false_positives()
        all_results.extend(false_positive_results)

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
        false_positive_passed = sum(1 for r in false_positive_results if r['status'] == "✅ PASS")

        print("\nПо категориям:")
        print(f"  Семантическая точность: {semantic_passed}/{len(semantic_results)}")
        print(f"  Грамматика/орфография: {grammar_passed}/{len(grammar_results)}")
        print(f"  Категориальная совместимость: {category_passed}/{len(category_results)}")
        print(f"  Отсечение ложных совпадений: {false_positive_passed}/{len(false_positive_results)}")

        return all_results


if __name__ == "__main__":
    tester = SimpleMatchingTester()
    results = tester.run_all_tests()
