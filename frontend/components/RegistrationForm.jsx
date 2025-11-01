import { useState } from 'react';
import { createListing } from '../services/api';

const CITIES = ['Алматы', 'Астана', 'Шымкент'];

const CATEGORIES = [
  'Техника и электроника',
  'Одежда и обувь',
  'Мебель и домашний быт',
  'Книги и медиа',
  'Спорт и активный отдых',
  'Услуги',
  'Продукты и питание',
  'Прочее'
];

export default function RegistrationForm({ onSubmit, onCancel }) {
  const [userData, setUserData] = useState({
    name: '',
    telegram: '',
    city: 'Алматы'
  });

  const [categories, setCategories] = useState(
    CATEGORIES.reduce((acc, cat) => {
      acc[cat] = { want: '', offer: '' };
      return acc;
    }, {})
  );

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleUserDataChange = (e) => {
    const { name, value } = e.target;
    setUserData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCategoryChange = (category, type, value) => {
    setCategories(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [type]: value
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Validate user data
      if (!userData.name.trim()) {
        throw new Error('ФИО обязательно');
      }
      if (!userData.telegram.trim()) {
        throw new Error('Телеграм контакт обязателен');
      }

      // Create listings for each category with content
      const listings = [];
      for (const [category, data] of Object.entries(categories)) {
        if (data.want.trim()) {
          listings.push(createListing({
            user_id: 1,
            listing_type: 'want',
            title: data.want,
            description: `${userData.name} ищет в категории: ${category}`,
            category: category,
            location: userData.city
          }));
        }
        if (data.offer.trim()) {
          listings.push(createListing({
            user_id: 1,
            listing_type: 'offer',
            title: data.offer,
            description: `${userData.name} предлагает в категории: ${category}`,
            category: category,
            location: userData.city
          }));
        }
      }

      if (listings.length === 0) {
        throw new Error('Заполните хотя бы одно поле');
      }

      // Submit all listings
      await Promise.all(listings);

      alert(`✅ Анкета успешно создана!\n${listings.length} объявлений опубликовано`);
      onSubmit();
    } catch (err) {
      console.error('Error:', err);
      setError(err.message);
      alert(`❌ Ошибка: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      padding: '30px',
      maxWidth: '1200px',
      margin: '20px auto'
    }}>
      <h1 style={{ textAlign: 'center', color: '#333', marginBottom: '30px' }}>
        📋 Заполните вашу анкету обмена
      </h1>

      <form onSubmit={handleSubmit}>
        {/* User Data Section */}
        <div style={{
          backgroundColor: '#f9f9f9',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '30px',
          border: '2px solid #ff9800'
        }}>
          <h2 style={{ marginTop: 0, color: '#ff9800' }}>👤 Ваши данные</h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                ФИО *
              </label>
              <input
                type="text"
                name="name"
                value={userData.name}
                onChange={handleUserDataChange}
                placeholder="Ваше полное имя"
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '4px',
                  border: '1px solid #ddd',
                  boxSizing: 'border-box',
                  fontSize: '14px'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Телеграм контакт *
              </label>
              <input
                type="text"
                name="telegram"
                value={userData.telegram}
                onChange={handleUserDataChange}
                placeholder="@username или +7..."
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '4px',
                  border: '1px solid #ddd',
                  boxSizing: 'border-box',
                  fontSize: '14px'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Город *
              </label>
              <select
                name="city"
                value={userData.city}
                onChange={handleUserDataChange}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '4px',
                  border: '1px solid #ddd',
                  boxSizing: 'border-box',
                  fontSize: '14px'
                }}
              >
                {CITIES.map(city => (
                  <option key={city} value={city}>{city}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Categories Section */}
        <div style={{ marginBottom: '30px' }}>
          <h2 style={{ color: '#333', marginBottom: '20px', textAlign: 'center' }}>
            📦 Категории обмена
          </h2>
          <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
            Слева введите что вам <span style={{ color: '#007bff', fontWeight: 'bold' }}>НУЖНО</span>,
            справа что вы <span style={{ color: '#28a745', fontWeight: 'bold' }}>ПРЕДЛАГАЕТЕ</span>.
            Оставляйте пустыми ненужные категории.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '15px' }}>
            {CATEGORIES.map(category => (
              <div key={category} style={{
                display: 'grid',
                gridTemplateColumns: '200px 1fr 1fr',
                gap: '15px',
                padding: '15px',
                backgroundColor: '#f9f9f9',
                borderRadius: '6px',
                border: '1px solid #eee',
                alignItems: 'center'
              }}>
                <div style={{
                  fontWeight: 'bold',
                  color: '#333',
                  fontSize: '14px',
                  padding: '5px'
                }}>
                  {category}
                </div>

                {/* Want column */}
                <input
                  type="text"
                  value={categories[category].want}
                  onChange={(e) => handleCategoryChange(category, 'want', e.target.value)}
                  placeholder="Что нужно получить?"
                  style={{
                    padding: '10px',
                    borderRadius: '4px',
                    border: '2px solid #007bff',
                    boxSizing: 'border-box',
                    fontSize: '14px',
                    backgroundColor: '#f0f7ff'
                  }}
                />

                {/* Offer column */}
                <input
                  type="text"
                  value={categories[category].offer}
                  onChange={(e) => handleCategoryChange(category, 'offer', e.target.value)}
                  placeholder="Что предлагаете?"
                  style={{
                    padding: '10px',
                    borderRadius: '4px',
                    border: '2px solid #28a745',
                    boxSizing: 'border-box',
                    fontSize: '14px',
                    backgroundColor: '#f0fff0'
                  }}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px',
          marginBottom: '30px',
          padding: '15px',
          backgroundColor: '#f0f7ff',
          borderRadius: '6px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              backgroundColor: '#007bff',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold'
            }}>
              ←
            </div>
            <div>
              <strong style={{ color: '#007bff' }}>НУЖНО</strong>
              <p style={{ margin: '2px 0', color: '#666', fontSize: '13px' }}>
                Что вы ищете?
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              backgroundColor: '#28a745',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold'
            }}>
              →
            </div>
            <div>
              <strong style={{ color: '#28a745' }}>ПРЕДЛАГАЮ</strong>
              <p style={{ margin: '2px 0', color: '#666', fontSize: '13px' }}>
                Что вы предлагаете?
              </p>
            </div>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div style={{
            padding: '15px',
            backgroundColor: '#fff3cd',
            color: '#856404',
            borderRadius: '4px',
            marginBottom: '20px',
            border: '1px solid #ffc107'
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Buttons */}
        <div style={{
          display: 'flex',
          gap: '10px',
          justifyContent: 'center'
        }}>
          <button
            type="submit"
            disabled={submitting}
            style={{
              padding: '15px 40px',
              backgroundColor: submitting ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: submitting ? 'not-allowed' : 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              transition: 'background-color 0.3s'
            }}
          >
            {submitting ? '⏳ Создание анкеты...' : '✓ Опубликовать анкету'}
          </button>

          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            style={{
              padding: '15px 40px',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            ✕ Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
