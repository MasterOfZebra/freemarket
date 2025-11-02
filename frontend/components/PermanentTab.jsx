import { useState } from 'react';
import { validatePermanentItem } from '../utils/validators';
import { PERMANENT_CATEGORIES } from './ExchangeTabs';
import { Alert, Button, Card, Input } from './ui';

/**
 * Initialize categories structure
 */
const initializeCategoriesByType = () => {
  const result = {};
  PERMANENT_CATEGORIES.forEach(group => {
    group.items.forEach(item => {
      result[item.value] = {
        label: item.label,
        group: group.group,
        enabled: false,
        items: []
      };
    });
  });
  return result;
};

export default function PermanentTab({ userId, onSubmit }) {
  const [wants, setWants] = useState(initializeCategoriesByType());
  const [offers, setOffers] = useState(initializeCategoriesByType());
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  // Toggle category enabled/disabled
  const toggleCategory = (side, categoryKey) => {
    const setter = side === 'wants' ? setWants : setOffers;
    setter(prev => ({
      ...prev,
      [categoryKey]: {
        ...prev[categoryKey],
        enabled: !prev[categoryKey].enabled
      }
    }));
  };

  // Add item to category
  const addItem = (side, categoryKey) => {
    const setter = side === 'wants' ? setWants : setOffers;
    setter(prev => ({
      ...prev,
      [categoryKey]: {
        ...prev[categoryKey],
        items: [...prev[categoryKey].items, { name: '', price: '' }]
      }
    }));
  };

  // Remove item from category
  const removeItem = (side, categoryKey, index) => {
    const setter = side === 'wants' ? setWants : setOffers;
    setter(prev => {
      const items = prev[categoryKey].items.filter((_, i) => i !== index);
      return {
        ...prev,
        [categoryKey]: { ...prev[categoryKey], items }
      };
    });
  };

  // Update item field
  const updateItem = (side, categoryKey, index, field, value) => {
    const setter = side === 'wants' ? setWants : setOffers;
    setter(prev => {
      const items = [...prev[categoryKey].items];
      items[index] = { ...items[index], [field]: value };
      return {
        ...prev,
        [categoryKey]: { ...prev[categoryKey], items }
      };
    });
  };

  const handleSubmit = async () => {
    setErrors([]);
    setLoading(true);

    try {
      // Validate items
      const newErrors = [];
      
      const validateCategory = (side, catData) => {
        if (!catData.enabled) return;
        catData.items.forEach((item, idx) => {
          if (item.name && item.price) {
            if (item.name.length < 3) {
              newErrors.push(`${side}: название слишком короткое`);
            }
            if (isNaN(parseInt(item.price)) || parseInt(item.price) < 1) {
              newErrors.push(`${side}: некорректная стоимость`);
            }
          } else if (item.name || item.price) {
            newErrors.push(`${side}: заполните название и стоимость`);
          }
        });
      };

      Object.entries(wants).forEach(([key, cat]) => validateCategory('WANTS', cat));
      Object.entries(offers).forEach(([key, cat]) => validateCategory('OFFERS', cat));

      // Check that at least something is filled
      const hasWants = Object.values(wants).some(cat => cat.items.length > 0);
      const hasOffers = Object.values(offers).some(cat => cat.items.length > 0);

      if (!hasWants && !hasOffers) {
        throw new Error('Добавьте хотя бы один предмет');
      }

      if (newErrors.length > 0) {
        setErrors(newErrors);
        setLoading(false);
        return;
      }

      // Transform to submission format
      const formattedWants = {};
      const formattedOffers = {};

      Object.entries(wants).forEach(([key, cat]) => {
        if (cat.enabled && cat.items.length > 0) {
          formattedWants[key] = cat.items.map(item => ({
            name: item.name.trim(),
            price: parseInt(item.price)
          }));
        }
      });

      Object.entries(offers).forEach(([key, cat]) => {
        if (cat.enabled && cat.items.length > 0) {
          formattedOffers[key] = cat.items.map(item => ({
            name: item.name.trim(),
            price: parseInt(item.price)
          }));
        }
      });

      onSubmit({
        wants: formattedWants,
        offers: formattedOffers
      });

    } finally {
      setLoading(false);
    }
  };

  // Render category section
  const renderCategorySection = (side, categoryKey, categoryData) => {
    const isWants = side === 'wants';
    const data = isWants ? wants : offers;
    
    return (
      <div key={categoryKey} className="border rounded p-4 mb-3 bg-gray-50">
        {/* Category Header */}
        <div className="flex items-center gap-3 mb-3">
          <input
            type="checkbox"
            checked={categoryData.enabled}
            onChange={() => toggleCategory(side, categoryKey)}
            className="w-5 h-5 rounded cursor-pointer"
          />
          <label className="font-semibold text-sm cursor-pointer flex-1">
            {categoryData.group} / {categoryData.label}
          </label>
          {categoryData.enabled && (
            <button
              type="button"
              onClick={() => addItem(side, categoryKey)}
              className="px-2 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
            >
              ➕ Добавить
            </button>
          )}
        </div>

        {/* Items List */}
        {categoryData.enabled && categoryData.items.length > 0 && (
          <div className="space-y-2 ml-8">
            {categoryData.items.map((item, idx) => (
              <div key={idx} className="flex gap-2 items-end">
                <input
                  type="text"
                  placeholder="Название предмета"
                  value={item.name}
                  onChange={(e) => updateItem(side, categoryKey, idx, 'name', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded text-sm"
                  minLength={3}
                  maxLength={100}
                />
                <input
                  type="number"
                  placeholder="Стоимость ₸"
                  value={item.price}
                  onChange={(e) => updateItem(side, categoryKey, idx, 'price', e.target.value)}
                  className="w-32 px-3 py-2 border rounded text-sm"
                  min={1}
                  max={10000000}
                />
                <button
                  type="button"
                  onClick={() => removeItem(side, categoryKey, idx)}
                  className="px-2 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                >
                  🗑
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {errors.length > 0 && (
        <Alert type="error">
          {errors.map((err, i) => <div key={i}>• {err}</div>)}
        </Alert>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* WANTS Section */}
        <div>
          <h3 className="text-lg font-bold mb-4 text-blue-600">🔵 НУЖНО (Wants)</h3>
          <div className="space-y-2">
            {Object.entries(wants).map(([key, cat]) =>
              renderCategorySection('wants', key, cat)
            )}
          </div>
        </div>

        {/* OFFERS Section */}
        <div>
          <h3 className="text-lg font-bold mb-4 text-green-600">🟢 ПРЕДЛАГАЮ (Offers)</h3>
          <div className="space-y-2">
            {Object.entries(offers).map(([key, cat]) =>
              renderCategorySection('offers', key, cat)
            )}
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-3 bg-orange-500 text-white font-bold rounded-lg hover:bg-orange-600 disabled:opacity-50"
      >
        {loading ? '⏳ Обработка...' : '🔍 Начать поиск'}
      </button>
    </div>
  );
}
