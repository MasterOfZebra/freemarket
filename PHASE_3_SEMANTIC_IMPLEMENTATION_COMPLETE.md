## Этап 3 — Semantic Matching (кратко)

Статус: ГОТОВО. Добавлен семантический слой, гибридное скорингование и авто-переобучение.

### Что сделано
- `semantic_embedder.py`: SentenceTransformer/fastText, функция `similarity(text1, text2)` и признаки (`semantic_similarity`).
- `model_predictor.py`: гибридная комбинация `final = 0.3*rule + 0.4*ml + 0.3*semantic` (настраиваемо).
- `feedback_manager.py`: `commit_to_training(auto_retrain=True)`, история версий, порог переобучения по фидбеку.
- `monitoring/semantic_diagnostics.py`: outliers, отчёты, CLI (`--outliers | --report`).

### Зависимости
```bash
pip install sentence-transformers fasttext
```

### Использование (минимум)
```python
from backend.matching.semantic_embedder import get_embedder
from backend.matching.model_predictor import combine_scores

emb = get_embedder()
sem = emb.similarity("велосипед горный", "велосипед городской")
final = combine_scores(rule_based_score=0.8, ml_score=0.7, semantic_score=sem)
```

### Диагностика (CLI)
```bash
python -m backend.monitoring.semantic_diagnostics --report
```

### Следующие шаги
- Сбор ≥100 размеченных пар с `semantic_similarity` и переобучение.
- A/B-тест гибридного скоринга.

Обновлено: 2025-01-30

