import { useState } from 'react';
import { validatePermanentItem } from '../utils/validators';
import { PERMANENT_CATEGORIES } from './ExchangeTabs';
import { Alert, Button, Card, Input, Select, Textarea } from './ui';

/**
 * @typedef {Object} ItemForm
 * @property {string} category
 * @property {string} item_name
 * @property {string} value_tenge
 * @property {string} description
 */

// Flatten categories for Select component
const getCategoryOptions = () => {
  const options = [];
  PERMANENT_CATEGORIES.forEach(group => {
    group.items.forEach(item => {
      options.push({ value: item.value, label: `${group.group} - ${item.label}` });
    });
  });
  return options;
};

const CATEGORY_OPTIONS = getCategoryOptions();

/**
 * @typedef {Object} PermanentTabProps
 * @property {number} userId
 * @property {function(Object): void} onSubmit
 */

export default function PermanentTab({ userId, onSubmit }) {
  const [wants, setWants] = useState([{ category: '', item_name: '', value_tenge: '', description: '' }]);
  const [offers, setOffers] = useState([{ category: '', item_name: '', value_tenge: '', description: '' }]);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAddItem = (type) => {
    const newItem = { category: '', item_name: '', value_tenge: '', description: '' };
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

  const handleItemChange = (type, index, field, value) => {
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
        if (item.item_name || item.category || item.value_tenge) {
          const validation = validatePermanentItem(item);
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

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">🟢 Постоянный обмен (без возврата)</h2>
      <p className="text-gray-600">Укажите предметы по их денежной стоимости</p>

      <div className="bg-green-50 p-3 rounded border-l-4 border-green-500">
        <p className="text-sm text-green-900">
          💰 <strong>Эквивалентность:</strong> Предметы сопоставляются по рыночной стоимости (value)
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
      <Card className="p-4 border-l-4 border-blue-500">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">📦 Что вы ищете (Хочу)</h3>
          <Button size="sm" onClick={() => handleAddItem('wants')}>+ Добавить</Button>
        </div>

        <div className="space-y-4">
          {wants.map((item, idx) => (
            <div key={idx} className="border rounded p-4 space-y-3 bg-blue-50">
              <div className="grid grid-cols-1 gap-3">
                <Select
                  label="Категория"
                  value={item.category}
                  onChange={(val) => handleItemChange('wants', idx, 'category', val)}
                  options={CATEGORY_OPTIONS}
                />
                <Input
                  label="Название предмета"
                  placeholder="Е.г. iPhone 13 Pro"
                  value={item.item_name}
                  onChange={(val) => handleItemChange('wants', idx, 'item_name', val)}
                  minLength={3}
                  maxLength={100}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Стоимость (₸)"
                  type="number"
                  placeholder="50000"
                  value={item.value_tenge}
                  onChange={(val) => handleItemChange('wants', idx, 'value_tenge', val)}
                  min={1}
                  max={10000000}
                />
                <div></div>
              </div>

              <Textarea
                label="Описание (опционально)"
                placeholder="Состояние, комплектация..."
                value={item.description}
                onChange={(val) => handleItemChange('wants', idx, 'description', val)}
                maxLength={500}
                rows={2}
              />

              {idx > 0 && (
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => handleRemoveItem('wants', idx)}
                >
                  ✕ Удалить
                </Button>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* OFFERS Section */}
      <Card className="p-4 border-l-4 border-green-500">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">📦 Что вы предлагаете (Могу)</h3>
          <Button size="sm" onClick={() => handleAddItem('offers')}>+ Добавить</Button>
        </div>

        <div className="space-y-4">
          {offers.map((item, idx) => (
            <div key={idx} className="border rounded p-4 space-y-3 bg-green-50">
              <div className="grid grid-cols-1 gap-3">
                <Select
                  label="Категория"
                  value={item.category}
                  onChange={(val) => handleItemChange('offers', idx, 'category', val)}
                  options={CATEGORY_OPTIONS}
                />
                <Input
                  label="Название предмета"
                  placeholder="Е.г. Письменный стол"
                  value={item.item_name}
                  onChange={(val) => handleItemChange('offers', idx, 'item_name', val)}
                  minLength={3}
                  maxLength={100}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Стоимость (₸)"
                  type="number"
                  placeholder="30000"
                  value={item.value_tenge}
                  onChange={(val) => handleItemChange('offers', idx, 'value_tenge', val)}
                  min={1}
                  max={10000000}
                />
                <div></div>
              </div>

              <Textarea
                label="Описание (опционально)"
                placeholder="Состояние, комплектация..."
                value={item.description}
                onChange={(val) => handleItemChange('offers', idx, 'description', val)}
                maxLength={500}
                rows={2}
              />

              {idx > 0 && (
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => handleRemoveItem('offers', idx)}
                >
                  ✕ Удалить
                </Button>
              )}
            </div>
          ))}
        </div>
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
