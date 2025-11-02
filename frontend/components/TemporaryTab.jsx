import { useState } from 'react';
import { validateTemporaryItem } from '../utils/validators';
import { TEMPORARY_CATEGORIES } from './ExchangeTabs';
import { Alert, Button, Card, Input, Select, Textarea } from './ui';

/**
 * @typedef {Object} TemporaryItemForm
 * @property {string} category
 * @property {string} item_name
 * @property {string} value_tenge
 * @property {string} duration_days
 * @property {string} description
 */

// Flatten categories for Select component
const getCategoryOptions = () => {
  const options = [];
  TEMPORARY_CATEGORIES.forEach((group) => {
    group.items.forEach((item) => {
      options.push({ value: item.value, label: `${group.group} - ${item.label}` });
    });
  });
  return options;
};

const CATEGORY_OPTIONS = getCategoryOptions();

/**
 * @typedef {Object} TemporaryTabProps
 * @property {number} userId
 * @property {function(Object): void} onSubmit
 */

export default function TemporaryTab({ userId, onSubmit }) {
  const [wants, setWants] = useState([
    { category: '', item_name: '', value_tenge: '', duration_days: '', description: '' }
  ]);
  const [offers, setOffers] = useState([
    { category: '', item_name: '', value_tenge: '', duration_days: '', description: '' }
  ]);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  const calculateDailyRate = (value, days) => {
    const v = parseFloat(value) || 0;
    const d = parseInt(days) || 0;
    if (!d || d <= 0) return 0;
    return v / d;
  };

  const handleAddItem = (type) => {
    const newItem = {
      category: '',
      item_name: '',
      value_tenge: '',
      duration_days: '',
      description: ''
    };
    if (type === 'wants') {
      setWants([...wants, newItem]);
    } else {
      setOffers([...offers, newItem]);
    }
  };

  const handleRemoveItem = (type, index) => {
    if (type === 'wants') {
      setWants(wants.filter((_, i) => i !== index));
    } else {
      setOffers(offers.filter((_, i) => i !== index));
    }
  };

  const handleItemChange = (
    type,
    index,
    field,
    value
  ) => {
    const items = type === 'wants' ? [...wants] : [...offers];
    items[index] = { ...items[index], [field]: value };
    if (type === 'wants') {
      setWants(items);
    } else {
      setOffers(items);
    }
  };

  const handleSubmit = async () => {
    setErrors([]);
    setLoading(true);

    try {
      // Validate all items
      const allItems = [...wants, ...offers];
      const newErrors: string[] = [];

      allItems.forEach((item, idx) => {
        if (item.item_name || item.category || item.value_tenge || item.duration_days) {
          const validation = validateTemporaryItem(item);
          if (!validation.valid) {
            newErrors.push(`Item ${idx}: ${validation.error}`);
          }
        }
      });

      if (newErrors.length > 0) {
        setErrors(newErrors);
        setLoading(false);
        return;
      }

      // Group by category
      const wantsByCategory = {};
      const offersByCategory = {};

      wants.forEach(item => {
        if (item.item_name && item.category) {
          if (!wantsByCategory[item.category]) {
            wantsByCategory[item.category] = [];
          }
          wantsByCategory[item.category].push(item);
        }
      });

      offers.forEach(item => {
        if (item.item_name && item.category) {
          if (!offersByCategory[item.category]) {
            offersByCategory[item.category] = [];
          }
          offersByCategory[item.category].push(item);
        }
      });

      onSubmit({
        wants: wantsByCategory,
        offers: offersByCategory
      });
    } finally {
      setLoading(false);
    }
  };

  const renderItemCard = (
    item,
    idx,
    type,
    bgColor
  ) => {
    const dailyRate = calculateDailyRate(item.value_tenge, item.duration_days);

    return (
      <div key={idx} className={`border rounded p-4 space-y-3 ${bgColor}`}>
        <div className="grid grid-cols-1 gap-3">
          <Select
            label="Категория"
            value={item.category}
            onChange={(val) => handleItemChange(type, idx, 'category', val)}
            options={CATEGORY_OPTIONS}
          />
          <Input
            label="Название предмета"
            placeholder="Е.г. Велосипед горный"
            value={item.item_name}
            onChange={(val) => handleItemChange(type, idx, 'item_name', val)}
            minLength={3}
            maxLength={100}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Базовая стоимость (₸)"
            type="number"
            placeholder="30000"
            value={item.value_tenge}
            onChange={(val) => handleItemChange(type, idx, 'value_tenge', val)}
            min={1}
            max={10000000}
          />
          <Input
            label="Дней аренды"
            type="number"
            placeholder="7"
            value={item.duration_days}
            onChange={(val) => handleItemChange(type, idx, 'duration_days', val)}
            min={1}
            max={365}
          />
        </div>

        {/* Auto-calculated daily rate display */}
        {item.value_tenge && item.duration_days && (
          <div className="bg-gradient-to-r from-blue-100 to-purple-100 p-3 rounded border-2 border-blue-300">
            <div className="text-sm text-gray-700">Дневной тариф:</div>
            <div className="text-2xl font-bold text-blue-600">
              {dailyRate.toFixed(2)} ₸/день
            </div>
            <div className="text-xs text-gray-600 mt-1">
              Расчёт: {item.value_tenge} ₸ ÷ {item.duration_days} дн = {dailyRate.toFixed(2)} ₸/дн
            </div>
          </div>
        )}

        <Textarea
          label="Описание (опционально)"
          placeholder="Состояние, комплектация..."
          value={item.description}
          onChange={(val) => handleItemChange(type, idx, 'description', val)}
          maxLength={500}
          rows={2}
        />

        {idx > 0 && (
          <Button
            size="sm"
            variant="danger"
            onClick={() => handleRemoveItem(type, idx)}
          >
            ✕ Удалить
          </Button>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">🟠 Временный обмен (с возвратом)</h2>
      <p className="text-gray-600">Предметы для краткосрочной аренды - укажите стоимость и период</p>

      <div className="bg-orange-50 p-3 rounded border-l-4 border-orange-500">
        <p className="text-sm text-orange-900">
          🕒 <strong>Эквивалентность:</strong> Предметы сопоставляются по дневному тарифу (value ÷ duration)
        </p>
      </div>

      {errors.length > 0 && (
        <Alert type="error">
          <ul className="list-disc pl-5">
            {errors.map((err, i) => <li key={i}>{err}</li>)}
          </ul>
        </Alert>
      )}

      {/* WANTS Section */}
      <Card className="p-4 border-l-4 border-orange-500">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">📦 Что вы хотите взять в аренду (Хочу)</h3>
          <Button size="sm" onClick={() => handleAddItem('wants')}>+ Добавить</Button>
        </div>

        <div className="space-y-4">
          {wants.map((item, idx) => renderItemCard(item, idx, 'wants', 'bg-orange-50'))}
        </div>
      </Card>

      {/* OFFERS Section */}
      <Card className="p-4 border-l-4 border-green-500">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">📦 Что вы предлагаете в аренду (Могу)</h3>
          <Button size="sm" onClick={() => handleAddItem('offers')}>+ Добавить</Button>
        </div>

        <div className="space-y-4">
          {offers.map((item, idx) => renderItemCard(item, idx, 'offers', 'bg-green-50'))}
        </div>
      </Card>

      {/* Info Box */}
      <Card className="p-4 bg-blue-50 border-l-4 border-blue-500">
        <h4 className="font-semibold text-blue-900 mb-2">💡 Как работает расчёт</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>✓ Введите базовую стоимость предмета и период аренды</li>
          <li>✓ Дневной тариф рассчитывается автоматически</li>
          <li>✓ Система подбирает партнёров с похожими дневными тарифами</li>
          <li>✓ Допускается отклонение ±15% (система учтёт это при поиске)</li>
        </ul>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end">
        <Button variant="secondary">Сохранить черновик</Button>
        <Button
          variant="primary"
          size="lg"
          loading={loading}
          onClick={handleSubmit}
        >
          🔍 Найти совпадения
        </Button>
      </div>
    </div>
  );
}
