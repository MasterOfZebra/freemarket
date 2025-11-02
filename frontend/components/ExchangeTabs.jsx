/**
 * ExchangeTabs.tsx
 * Main tab container for Permanent and Temporary Exchange
 *
 * Features:
 * - Two-tab UI (Green for Permanent, Orange for Temporary)
 * - Form validation
 * - API integration
 */
import React, { useState } from 'react';
import PermanentTab from './PermanentTab';
import TemporaryTab from './TemporaryTab';
import { apiService } from '../services/api';

// ========== EXPANDED CATEGORY SYSTEM ==========

// 🕒 TEMPORARY EXCHANGE (с возвратом)
export const TEMPORARY_CATEGORIES = [
  {
    group: '🚗 Транспорт и мобильность', items: [
      { value: 'bicycle', label: 'Велосипеды, самокаты, гироскутеры' },
      { value: 'electric_transport', label: 'Электросамокаты, мопеды' },
      { value: 'sports_transport', label: 'Спортивные и детские средства передвижения' }
    ]
  },
  {
    group: '🔧 Инструменты и оборудование', items: [
      { value: 'hand_tools', label: 'Ручные инструменты' },
      { value: 'power_tools', label: 'Электроинструменты' },
      { value: 'industrial_equipment', label: '3D-принтеры, станки, проектное оборудование' }
    ]
  },
  {
    group: '📷 Фото-, видео-, аудио-техника', items: [
      { value: 'photo_video', label: 'Фотоаппараты, объективы, дроны' },
      { value: 'audio_equipment', label: 'Микрофоны, рекордеры, свет' }
    ]
  },
  {
    group: '⛷️ Спорт и активный отдых', items: [
      { value: 'sports_gear', label: 'Спортивный инвентарь (лыжи, палатки, велосипеды)' },
      { value: 'tourism_camping', label: 'Туристические наборы, кемпинг' }
    ]
  },
  {
    group: '🎮 Развлечения и хобби', items: [
      { value: 'games_vr', label: 'Настольные игры, консоли, VR' },
      { value: 'music_instruments', label: 'Музыкальные инструменты для сессий' }
    ]
  },
  {
    group: '👗 Одежда и аксессуары', items: [
      { value: 'costumes', label: 'Костюмы, сценическая одежда' },
      { value: 'event_accessories', label: 'Украшения, часы, сумки для мероприятий' }
    ]
  },
  {
    group: '💳 Цифровые и финансовые активы', items: [
      { value: 'subscriptions', label: 'Подписки, лицензии, токены доступа' },
      { value: 'temporary_loan', label: 'Временный займ (деньги ↔ предмет на срок)' }
    ]
  },
  {
    group: '📚 Услуги и навыки', items: [
      { value: 'consulting', label: 'Временная помощь, репетиторство, консультация' }
    ]
  }
];

// 💰 PERMANENT EXCHANGE (без возврата)
export const PERMANENT_CATEGORIES = [
  {
    group: '🚗 Транспорт', items: [
      { value: 'cars', label: 'Автомобили, мотоциклы, спецтехника' }
    ]
  },
  {
    group: '🏠 Недвижимость', items: [
      { value: 'real_estate', label: 'Квартиры, дома, участки, гаражи' }
    ]
  },
  {
    group: '💻 Техника и электроника', items: [
      { value: 'electronics', label: 'Смартфоны, ноутбуки, бытовая техника' },
      { value: 'entertainment_tech', label: 'ТВ, консоли, гаджеты' }
    ]
  },
  {
    group: '👕 Одежда и личные вещи', items: [
      { value: 'everyday_clothes', label: 'Повседневная одежда, обувь' },
      { value: 'accessories', label: 'Личные аксессуары' }
    ]
  },
  {
    group: '🛋️ Предметы быта и мебель', items: [
      { value: 'kitchen_furniture', label: 'Кухонная техника, мебель, текстиль' }
    ]
  },
  {
    group: '🎨 Хобби и коллекции', items: [
      { value: 'collectibles', label: 'Коллекционные предметы, картины, антиквариат' }
    ]
  },
  {
    group: '🐾 Живое и растения', items: [
      { value: 'animals_plants', label: 'Домашние животные и растения (постоянная ответственность)' }
    ]
  },
  {
    group: '💰 Финансы и цифровые активы', items: [
      { value: 'money_crypto', label: 'Деньги, криптовалюта, токены' },
      { value: 'securities', label: 'Ценные бумаги, доли, активы' }
    ]
  }
];

// Type definitions for JavaScript
/**
 * @typedef {Object} UserData
 * @property {string} name - User full name
 * @property {string} telegram - Telegram contact
 * @property {'Алматы'|'Астана'|'Шымкент'} city - User city
 */

/**
 * @typedef {Object} ExchangeTabsProps
 * @property {number} userId - User ID
 * @property {function(number): void} [onMatchesFound] - Callback for matches found
 */

/**
 * Transform form data to API format
 * Converts frontend form data structure to backend API expected format
 */
const transformFormDataToApiFormat = (
  formData,
  exchangeType,
  userData
) => {
  const result = {
    wants: {},
    offers: {},
    locations: [userData.city]
  };

  // Transform wants
  Object.entries(formData.wants || {}).forEach(([category, items]) => {
    if (Array.isArray(items) && items.length > 0) {
      result.wants[category] = items.map(item => ({
        category,
        exchange_type: exchangeType,
        item_name: item.name.trim(),
        value_tenge: parseInt(item.price) || 0,
        duration_days: exchangeType === 'temporary'
          ? (parseInt(item.duration_days) || null)
          : null,
        description: (item.description || '').trim()
      }));
    }
  });

  // Transform offers
  Object.entries(formData.offers || {}).forEach(([category, items]) => {
    if (Array.isArray(items) && items.length > 0) {
      result.offers[category] = items.map(item => ({
        category,
        exchange_type: exchangeType,
        item_name: item.name.trim(),
        value_tenge: parseInt(item.price) || 0,
        duration_days: exchangeType === 'temporary'
          ? (parseInt(item.duration_days) || null)
          : null,
        description: (item.description || '').trim()
      }));
    }
  });

  return result;
};

export default function ExchangeTabs({ userId, onMatchesFound }) {
  const [activeTab, setActiveTab] = useState('permanent');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [userData, setUserData] = useState({
    name: '',
    telegram: '',
    city: '' // Changed to single city
  });

  const handleUserDataChange = (field, value) => {
    if (field === 'city') {
      setUserData(prev => ({
        ...prev,
        city: value
      }));
    } else {
      setUserData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleTabChange = (value) => {
    setActiveTab(value);
    setError(null);
    setSuccess(false);
  };

  const handleSubmit = async (data) => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // Validate user data
      if (!userData.name.trim()) {
        throw new Error('Заполните ФИО');
      }
      if (!userData.telegram.trim()) {
        throw new Error('Заполните телеграм контакт');
      }
      if (!userData.city) {
        throw new Error('Выберите город');
      }

      // 1. Transform form data to API format
      const apiData = transformFormDataToApiFormat(data, activeTab, userData);

      // Validate that we have at least some items
      const totalWants = Object.values(apiData.wants).reduce((sum, arr) => sum + arr.length, 0);
      const totalOffers = Object.values(apiData.offers).reduce((sum, arr) => sum + arr.length, 0);

      if (totalWants === 0 && totalOffers === 0) {
        throw new Error('Добавьте хотя бы один предмет в раздел "Хочу" или "Могу"');
      }

      // 2. Send to backend API
      const response = await apiService.createListing({
        user_id: userId,
        wants: apiData.wants,
        offers: apiData.offers,
        locations: [userData.city], // Send as array with single city
        user_data: {
          name: userData.name,
          telegram: userData.telegram,
          city: userData.city
        }
      });

      console.log('Listing created:', response);

      // 3. Automatically trigger matching
      let matchesCount = 0;
      try {
        const matchesResponse = await apiService.findMatches(userId, activeTab);
        matchesCount = matchesResponse.matches_found || matchesResponse.total_matches || 0;
        console.log('Matches found:', matchesCount);
      } catch (matchError) {
        console.warn('Matching failed (listing still created):', matchError);
        // Don't fail the whole operation if matching fails
      }

      // 4. Update UI
      setSuccess(true);
      if (onMatchesFound) {
        onMatchesFound(matchesCount);
      }

      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(false), 5000);

    } catch (err) {
      console.error('Failed to submit listing:', err);
      setError(err.message || 'Ошибка при создании объявления. Попробуйте еще раз.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      <div className="border-0 shadow-lg bg-white rounded-lg p-6">
        <div className="pb-3">
          <h1 className="text-3xl font-bold">🎁 FreeMarket Exchange</h1>
          <p className="text-gray-600 mt-2">Выберите тип обмена и добавьте ваши предметы</p>
        </div>

        {/* User Data Form */}
        <div className="mb-6 p-4 bg-gradient-to-r from-orange-50 to-yellow-50 rounded-lg border-2 border-orange-300">
          <h2 className="text-xl font-bold mb-4 text-orange-800">👤 Ваши данные</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ФИО *
              </label>
              <input
                type="text"
                value={userData.name}
                onChange={(e) => handleUserDataChange('name', e.target.value)}
                placeholder="Ваше полное имя"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Телеграм контакт *
              </label>
              <input
                type="text"
                value={userData.telegram}
                onChange={(e) => handleUserDataChange('telegram', e.target.value)}
                placeholder="@username или +7..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Город *
              </label>
              <select
                value={userData.city}
                onChange={(e) => handleUserDataChange('city', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                required
              >
                <option value="">Выберите город</option>
                <option value="Алматы">Алматы</option>
                <option value="Астана">Астана</option>
                <option value="Шымкент">Шымкент</option>
              </select>
            </div>
          </div>
        </div>

        <div className="w-full">
          {/* Tab Triggers */}
          <div className="grid w-full grid-cols-2 mb-6 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => handleTabChange('permanent')}
              className={`flex items-center gap-2 justify-center py-2 px-4 rounded transition-all ${activeTab === 'permanent' ? 'bg-green-500 text-white' : 'bg-transparent'
                }`}
            >
              <span className="text-2xl">🟢</span>
              <span className="hidden sm:inline">Постоянный обмен</span>
              <span className="sm:hidden">Постоянный</span>
            </button>

            <button
              onClick={() => handleTabChange('temporary')}
              className={`flex items-center gap-2 justify-center py-2 px-4 rounded transition-all ${activeTab === 'temporary' ? 'bg-orange-500 text-white' : 'bg-transparent'
                }`}
            >
              <span className="text-2xl">🟠</span>
              <span className="hidden sm:inline">Временный обмен</span>
              <span className="sm:hidden">Временный</span>
            </button>
          </div>

          {/* Permanent Exchange Tab */}
          {activeTab === 'permanent' && (
            <div className="mt-6">
              <PermanentTab
                userId={userId}
                onSubmit={handleSubmit}
              />
            </div>
          )}

          {/* Temporary Exchange Tab */}
          {activeTab === 'temporary' && (
            <div className="mt-6">
              <TemporaryTab
                userId={userId}
                onSubmit={handleSubmit}
              />
            </div>
          )}
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 rounded">
          <p className="text-sm text-red-700">
          ❌ <strong>Ошибка:</strong> {error}
          </p>
        </div>
      )}

      {success && (
        <div className="mt-6 p-4 bg-green-50 border-l-4 border-green-500 rounded">
          <p className="text-sm text-green-700">
          ✅ <strong>Успешно!</strong> Объявление создано. Система автоматически ищет совпадения.
          </p>
        </div>
      )}

      {loading && (
        <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
          <p className="text-sm text-blue-700">
          ⏳ Обработка данных и поиск совпадений...
          </p>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
        <p className="text-sm text-gray-700">
          💡 <strong>Совет:</strong> Добавьте несколько предметов в обе категории (Хочу/Могу),
          затем нажмите "Найти совпадения" чтобы найти партнеров для обмена.
        </p>
      </div>
    </div>
  );
}
