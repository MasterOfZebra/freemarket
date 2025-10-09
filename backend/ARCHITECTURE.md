# FreeMarket Architecture v2.0

## Обзор системы

FreeMarket - это платформа для бартерного обмена товарами и услугами с использованием продвинутого ML-матчинга, фоновой обработки задач и автоматического обнаружения взаимных совпадений.

## Архитектура

### Компоненты

#### 1. FastAPI Backend
- **Роль**: REST API для клиентских приложений
- **Технологии**: FastAPI, Pydantic, SQLAlchemy
- **Основные эндпоинты**:
  - `/items` - управление предложениями
  - `/matches/{item_id}/optimal` - получение матчей с объяснениями
  - `/mutual-matches/{user_id}` - взаимные совпадения
  - `/matches/{match_id}/accept` - принятие матча

#### 2. PostgreSQL Database
- **Схема**:
  - `users` - пользователи
  - `items` - предложения (offers/wants)
  - `matches` - совпадения
  - `mutual_matches` - взаимные матчи
  - `notifications` - уведомления
  - `ab_metrics` - A/B тестовые метрики
  - `exchange_chains` - цепочки многосторонних обменов
  - `api_metrics` - метрики производительности

#### 3. Redis Queue
- **Роль**: Очередь фоновых задач
- **Ключевые очереди**:
  - `task_queue` - общая очередь задач
- **Кеш**:
  - Эмбеддинги текста (TTL 1 час)
  - Активные офферы по категориям (TTL 1 час)

#### 4. Background Worker
- **Роль**: Обработка фоновых задач
- **Задачи**:
  - `match_offer` - матчинг нового оффера
  - `cleanup_old_matches` - очистка старых матчей
  - `update_match_status` - обновление статуса матча

#### 5. ML Matching Engine
- **Компоненты**:
  - **Sentence-BERT**: Эмбеддинги текста
  - **LightGBM**: Learn-to-rank модель
  - **NetworkX**: Графовые алгоритмы для цепочек
- **Фичи скоринга**:
  - Текстовая схожесть
  - Совпадение тегов (wants/offers)
  - Пересечение ценовых диапазонов
  - Плотность диапазонов
  - Доверие пользователей

#### 6. A/B Testing Framework
- **Конфигурации**:
  - `control`: threshold 0.5, top_k 5
  - `variant_a`: threshold 0.6, top_k 3
  - `variant_b`: threshold 0.4, top_k 7
- **Метрики**:
  - Match accept rate
  - Conversion rate
  - Time to match
- **Автонастройка**: Периодическая корректировка порогов на основе метрик

#### 7. Notification System
- **Каналы**: Telegram
- **Типы уведомлений**:
  - `mutual_match` - взаимное совпадение
  - `match_improved` - улучшение скора матча

### Поток данных

1. **Создание оффера**:
   - POST /items → enqueue "match_offer" → worker матчит → создает matches/mutual_matches → отправляет notifications

2. **Получение матчей**:
   - GET /matches/{item_id}/optimal → match_for_item() → возвращает матчи с объяснениями

3. **Принятие матча**:
   - POST /matches/{match_id}/accept → обновляет статус → может создать mutual_match

### Масштабирование

- **Горизонтальное**: Множество worker инстансов
- **Кеш**: Redis для эмбеддингов и активных офферов
- **База**: GIN индексы для полнотекстового поиска
- **Мониторинг**: api_metrics таблица для latency tracking

### Безопасность

- Валидация через Pydantic
- SQL инъекции предотвращены SQLAlchemy
- Контакты раскрываются только при mutual match

### Мониторинг

- API метрики в PostgreSQL
- Логи в stdout/stderr
- Flower для Redis queue (опционально)

## Roadmap

### Sprint 1 ✅
- Динамические веса скоринга (learn-to-rank)
- Value density и currency normalization
- Инкрементальный матчинг с кешем
- TTL для эмбеддингов
- Улучшенные уведомления
- E2E тест полного потока
- Мониторинг воркеров

### Sprint 2 ✅
- A/B метрики и автоподбор порогов
- Match Preview с объяснениями
- Графовый матчинг (max_weight_matching)
- Таблица exchange_chains
- Метрики времени отклика
- Property-based тесты
- Документация v2
