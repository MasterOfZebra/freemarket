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

// 🕒 TEMPORARY EXCHANGE (с возвратом) - v6 система категорий
export const TEMPORARY_CATEGORIES = [
  {
    group: '🚗 Транспорт и мобильность', items: [
      { value: 'bicycles', label: 'Велосипеды, самокаты, гироскутеры' },
      { value: 'electric_transport', label: 'Электросамокаты, электровелосипеды' },
      { value: 'carsharing', label: 'Каршеринг, аренда прицепов, спецтехники' }
    ]
  },
  {
    group: '🔧 Инструменты и оборудование', items: [
      { value: 'hand_tools', label: 'Ручные и электроинструменты' },
      { value: 'printers_equipment', label: '3D-принтеры, станки, лабораторное оборудование' },
      { value: 'construction_tools', label: 'Оснащение для стройки, ремонта, мероприятий' }
    ]
  },
  {
    group: '📷 Фото-, видео-, аудио-техника', items: [
      { value: 'photo_equipment', label: 'Фотоаппараты, объективы, дроны' },
      { value: 'video_audio', label: 'Свет, звук, микрофоны, рекордеры' },
      { value: 'production_kits', label: 'Комплекты для съёмок, трансляций, подкастов' }
    ]
  },
  {
    group: '💻 Цифровые и вычислительные ресурсы', items: [
      { value: 'cloud_resources', label: 'Облачные GPU/CPU, хостинг, storage' },
      { value: 'api_access', label: 'Временный доступ к API, ML-моделям, инструментам' },
      { value: 'software_licenses', label: 'Подписки, лицензии, токены с ограниченным сроком' },
      { value: 'network_resources', label: 'Сетевые или энергетические мощности, интернет-каналы' }
    ]
  },
  {
    group: '💸 Финансы и взаимные займы', items: [
      { value: 'money_crypto', label: 'Деньги, криптовалюта, токены — с возвратом в том же объёме' },
      { value: 'trusted_equivalent', label: 'Используются как доверенный эквивалент ресурса' }
    ]
  },
  {
    group: '👥 Услуги и навыки', items: [
      { value: 'tutoring', label: 'Репетиторство, консультации, менторство' },
      { value: 'task_execution', label: 'Исполнение задач, помощь, участие в проектах' },
      { value: 'time_resource', label: 'Время человека как ограниченный ресурс' }
    ]
  },
  {
    group: '🏠 Пространства и помещения', items: [
      { value: 'housing_rental', label: 'Аренда жилья, офисов, складов' },
      { value: 'coworking_spaces', label: 'Коворкинги, студии, площадки для мероприятий' }
    ]
  },
  {
    group: '🐾 Уход за живыми объектами', items: [
      { value: 'pet_sitting', label: 'Передержка питомцев, полив растений' },
      { value: 'temporary_care', label: 'Временный уход' }
    ]
  },
  {
    group: '🎯 Спорт, отдых и досуг', items: [
      { value: 'sports_equipment', label: 'Спортивный инвентарь, палатки, кемпинг' },
      { value: 'board_games', label: 'Настольные игры, VR, музыкальные инструменты' },
      { value: 'props_rental', label: 'Прокат реквизита, костюмов, сценических аксессуаров' }
    ]
  }
];

// 💰 PERMANENT EXCHANGE (без возврата) - v6 система категорий
export const PERMANENT_CATEGORIES = [
  {
    group: '🚗 Транспорт и техника', items: [
      { value: 'personal_transport', label: 'Личные и спецтранспортные средства' },
      { value: 'electric_vehicles', label: 'Электротранспорт, дроны, техника для хобби' },
      { value: 'parts_consumables', label: 'Запчасти, комплектующие, расходники' }
    ]
  },
  {
    group: '🔧 Инструменты и оборудование', items: [
      { value: 'hand_power_tools', label: 'Ручные, электро-, строительные, лабораторные инструменты' },
      { value: 'production_facilities', label: 'Производственные и ремесленные установки' },
      { value: 'building_materials', label: 'Строительные материалы и элементы (двери, окна, панели, крепёж)' }
    ]
  },
  {
    group: '📷 Фото-, видео-, аудио-техника', items: [
      { value: 'photo_equipment', label: 'Фотоаппараты, оптика, микрофоны' },
      { value: 'lighting_equipment', label: 'Осветительные приборы, звукозаписывающая техника' }
    ]
  },
  {
    group: '💾 Цифровые, креативные и интеллектуальные активы', items: [
      { value: 'software_programs', label: 'Программы, исходный код, шаблоны, дизайн' },
      { value: 'media_content', label: 'Медиа, музыка, видео, NFT, цифровые коллекции' },
      { value: 'intellectual_property', label: 'Авторские права, бессрочные лицензии' }
    ]
  },
  {
    group: '👥 Услуги и навыки', items: [
      { value: 'completed_projects', label: 'Завершённые проекты, контент, дизайн, разработка' },
      { value: 'services_work', label: 'Ремонт, монтаж, обучение — с передачей результата' }
    ]
  },
  {
    group: '🏠 Недвижимость и пространство', items: [
      { value: 'property', label: 'Земля, дома, квартиры, студии, гаражи' },
      { value: 'property_rights', label: 'Право собственности или доля' }
    ]
  },
  {
    group: '🪴 Дом, сад и строительство', items: [
      { value: 'garden_equipment', label: 'Садовая техника, полив, мебель для сада' },
      { value: 'decor_elements', label: 'Декор, ограждения, строительные материалы' }
    ]
  },
  {
    group: '🛋️ Быт, мебель и интерьер', items: [
      { value: 'furniture_appliances', label: 'Мебель, бытовая техника, освещение' },
      { value: 'decor_textiles', label: 'Декор, текстиль, ковры, зеркала' }
    ]
  },
  {
    group: '👕 Одежда, мода и личные вещи', items: [
      { value: 'clothing_footwear', label: 'Одежда, обувь, аксессуары, украшения' },
      { value: 'vintage_luxury', label: 'Винтаж, мода premium, коллекционные вещи' }
    ]
  },
  {
    group: '🎮 Хобби, игры и коллекции', items: [
      { value: 'games_collectibles', label: 'Настольные игры, фигурки, комиксы, карточки' },
      { value: 'models_merch', label: 'Модели, игрушки, фан-мерч, подписные наборы' }
    ]
  },
  {
    group: '📚 Книги, музыка и медиа', items: [
      { value: 'physical_media', label: 'Книги, журналы, ноты, винил, CD, DVD' },
      { value: 'antiques_rare', label: 'Антикварные и редкие издания' }
    ]
  },
  {
    group: '🧴 Здоровье, красота и уход', items: [
      { value: 'beauty_cosmetics', label: 'Косметика, парфюмерия, уходовые гаджеты' },
      { value: 'health_devices', label: 'Аппараты для здоровья, wellness-техника' }
    ]
  },
  {
    group: '🌱 Живые объекты и природа', items: [
      { value: 'plants_animals', label: 'Растения, семена, питомцы, аквариумные объекты' },
      { value: 'breeding_care', label: 'Разведение и уход' }
    ]
  },
  {
    group: '🍎 Продукты и сельхозтовары', items: [
      { value: 'farm_products', label: 'Фермерская продукция, заготовки, мед, зерно, семена' },
      { value: 'natural_resources', label: 'Обмен натуральными продуктами и ресурсами' }
    ]
  },
  {
    group: '📚 Образовательные ресурсы и знания', items: [
      { value: 'courses_materials', label: 'Курсы, методики, учебные материалы, книги' },
      { value: 'intellectual_constructions', label: 'Авторские наработки, интеллектуальные конструкции' }
    ]
  },
  {
    group: '⚖️ Финансы и ценные активы', items: [
      { value: 'money_crypto', label: 'Деньги, криптовалюта, токены' },
      { value: 'securities_assets', label: 'Ценные бумаги, доли, активы' }
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

export default function ExchangeTabs({ userId, onMatchesFound, onListingCreated }) {
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
      
      // Notify parent component that listing was created (to refresh cabinet)
      if (onListingCreated) {
        onListingCreated();
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
              <span className="hidden md:inline">Постоянный обмен</span>
              <span className="md:hidden">Постоянный</span>
            </button>

            <button
              onClick={() => handleTabChange('temporary')}
              className={`flex items-center gap-2 justify-center py-2 px-4 rounded transition-all ${activeTab === 'temporary' ? 'bg-orange-500 text-white' : 'bg-transparent'
                }`}
            >
              <span className="text-2xl">🟠</span>
              <span className="hidden md:inline">Временный обмен</span>
              <span className="md:hidden">Временный</span>
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
