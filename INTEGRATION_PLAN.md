# План интеграции Permanent/Temporary Exchange в единую систему

## 📋 Текущее состояние

### ✅ Что уже есть:
1. **Backend:**
   - `ExchangeType` enum (PERMANENT/TEMPORARY)
   - `/api/listings/create-by-categories` endpoint с поддержкой exchange_type
   - `/api/listings/find-matches/{user_id}` с фильтрацией по exchange_type
   - Matching логика разделена по типам обмена
   - Модель `User` с полями: username, telegram_id, locations

2. **Frontend:**
   - `ExchangeTabs.tsx` - компонент с двумя вкладками
   - `PermanentTab.tsx` - форма для постоянного обмена
   - `TemporaryTab.tsx` - форма для временного обмена
   - `PERMANENT_CATEGORIES` и `TEMPORARY_CATEGORIES` определены
   - `apiService.createListing()` использует правильный endpoint

### ❌ Что нужно исправить:
1. **App.jsx** использует старый `RegistrationForm` вместо `ExchangeTabs`
2. **ExchangeTabs** не имеет формы пользователя (ФИО, телеграм, город)
3. **PermanentTab/TemporaryTab** не передают данные пользователя
4. **RegistrationForm.jsx** не использует правильные категории и exchange_type

## 🎯 План реализации

### Этап 1: Добавить форму пользователя в ExchangeTabs
**Файл:** `frontend/components/ExchangeTabs.tsx`

**Изменения:**
- Добавить состояние `userData` (name, telegram, city)
- Добавить форму вверху компонента перед вкладками
- Форма должна быть обязательной для заполнения
- Город - dropdown с 3 городами: Алматы, Астана, Шымкент

**Структура:**
```tsx
interface UserData {
  name: string;
  telegram: string;
  city: 'Алматы' | 'Астана' | 'Шымкент';
}
```

### Этап 2: Обновить PermanentTab и TemporaryTab
**Файлы:** `frontend/components/PermanentTab.tsx`, `frontend/components/TemporaryTab.tsx`

**Изменения:**
- Принять `userData` как prop
- Передать `userData` вместе с данными формы в `onSubmit`
- Убедиться что `locations` передается как массив с одним городом

### Этап 3: Обновить transformFormDataToApiFormat
**Файл:** `frontend/components/ExchangeTabs.tsx`

**Изменения:**
- Добавить `userData` в параметры функции
- Добавить `locations: [userData.city]` в возвращаемый объект
- Убедиться что `exchange_type` правильно устанавливается (permanent/temporary)

### Этап 4: Обновить App.jsx
**Файл:** `frontend/App.jsx`

**Изменения:**
- Удалить импорт `RegistrationForm`
- Добавить импорт `ExchangeTabs`
- Заменить `RegistrationForm` на `ExchangeTabs`
- Убрать старую логику с простыми wants/offers
- Оставить только список существующих объявлений (опционально)

### Этап 5: Обновить backend для сохранения данных пользователя
**Файл:** `backend/api/endpoints/listings_exchange.py`

**Изменения:**
- Убедиться что при создании listing обновляется User с:
  - `username` = userData.name
  - `telegram_username` = userData.telegram (если начинается с @)
  - `telegram_id` = userData.telegram (если это число)
  - `locations` = [userData.city]

### Этап 6: Проверить matching
**Файл:** `backend/api/endpoints/listings_exchange.py`

**Проверка:**
- `/api/listings/find-matches/{user_id}?exchange_type=permanent` работает отдельно
- `/api/listings/find-matches/{user_id}?exchange_type=temporary` работает отдельно
- Permanent matching не показывает temporary результаты и наоборот

## 📝 Детальный план изменений

### Шаг 1: ExchangeTabs.tsx - добавить форму пользователя
```tsx
// Добавить после строки 163
const [userData, setUserData] = useState<UserData>({
  name: '',
  telegram: '',
  city: 'Алматы'
});

// Добавить валидацию перед handleSubmit
if (!userData.name.trim() || !userData.telegram.trim()) {
  setError('Заполните ФИО и телеграм контакт');
  return;
}
```

### Шаг 2: PermanentTab.tsx - передать userData
```tsx
interface PermanentTabProps {
  userId: number;
  userData: UserData; // Добавить
  onSubmit: (data: { wants: ..., offers: ..., userData: UserData }) => void;
}
```

### Шаг 3: App.jsx - заменить RegistrationForm
```tsx
// Удалить
import RegistrationForm from './components/RegistrationForm';

// Добавить
import ExchangeTabs from './components/ExchangeTabs';

// Заменить рендер
{showRegistration && (
  <ExchangeTabs userId={1} onMatchesFound={handleMatchesFound} />
)}
```

### Шаг 4: Backend - обновить User при создании listing
```python
# В create_listing_by_categories после строки 82
if user_data := listing.user_data:  # Если передается
    user.username = user_data.get('name')
    user.locations = [user_data.get('city')]
    # Обработать telegram
```

## ✅ Критерии успеха

1. ✅ Пользователь видит форму с ФИО, телеграм, город вверху
2. ✅ Выбор между Permanent/Temporary через вкладки
3. ✅ Каждая вкладка показывает свои категории
4. ✅ При отправке создается listing с правильным exchange_type
5. ✅ Matching работает отдельно для каждого типа
6. ✅ Данные пользователя сохраняются в User модель
7. ✅ После создания listing показываются совпадения

## 🔄 Порядок выполнения

1. **Шаг 1-3:** Обновить ExchangeTabs, PermanentTab, TemporaryTab
2. **Шаг 4:** Обновить App.jsx
3. **Шаг 5:** Обновить backend для сохранения userData
4. **Шаг 6:** Тестирование и проверка matching

## 🧪 Тестирование

1. Заполнить форму пользователя
2. Выбрать Permanent tab, добавить несколько предметов
3. Выбрать Temporary tab, добавить несколько предметов
4. Отправить форму
5. Проверить что создались 2 отдельных listing с разными exchange_type
6. Проверить что matching для permanent не показывает temporary
7. Проверить что данные пользователя сохранились

