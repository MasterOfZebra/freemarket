import { useState } from 'react';

export function RegistrationPage({ onRegistrationComplete }) {
    const [formData, setFormData] = useState({
        fio: '',
        telegram: '',
        locations: []
    });
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const CITIES = ['Алматы', 'Астана', 'Шымкент'];

    const handleLocationChange = (city) => {
        setFormData(prev => ({
            ...prev,
            locations: prev.locations.includes(city)
                ? prev.locations.filter(c => c !== city)
                : [...prev.locations, city]
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        // Validation
        if (!formData.fio.trim()) {
            setError('Пожалуйста, введите ФИО');
            setLoading(false);
            return;
        }

        if (!formData.telegram.trim()) {
            setError('Пожалуйста, введите контакт Телеграма');
            setLoading(false);
            return;
        }

        if (!formData.telegram.startsWith('@')) {
            setError('Контакт должен начинаться с @');
            setLoading(false);
            return;
        }

        if (formData.locations.length === 0) {
            setError('Пожалуйста, выберите хотя бы один город');
            setLoading(false);
            return;
        }

        try {
            const response = await fetch('/api/users/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: formData.fio,
                    contact: formData.telegram,
                    locations: formData.locations
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при создании пользователя');
            }

            const userData = await response.json();
            console.log('✅ User created:', userData);

            localStorage.setItem('userId', userData.id);
            localStorage.setItem('userName', formData.fio);

            setSubmitted(true);
            setTimeout(() => {
                onRegistrationComplete(userData.id);
            }, 1500);
        } catch (err) {
            setError('❌ Ошибка: ' + err.message);
            console.error('Registration error:', err);
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div style={{
                maxWidth: '500px',
                margin: '50px auto',
                padding: '40px',
                textAlign: 'center',
                backgroundColor: '#e8f5e9',
                borderRadius: '8px',
                border: '2px solid #28a745'
            }}>
                <h2 style={{ color: '#28a745', marginBottom: '20px' }}>✅ Анкета отправлена!</h2>
                <p style={{ fontSize: '16px', marginBottom: '10px' }}>
                    Добро пожаловать, {formData.fio}!
                </p>
                <p style={{ fontSize: '14px', color: '#666' }}>
                    Сейчас вы будете перенаправлены на форму добавления товаров...
                </p>
                <div style={{ marginTop: '20px', fontSize: '24px' }}>⏳</div>
            </div>
        );
    }

    return (
        <div style={{
            maxWidth: '600px',
            margin: '0 auto',
            padding: '40px 20px',
            minHeight: '100vh',
            backgroundColor: '#f5f5f5'
        }}>
            <div style={{
                backgroundColor: 'white',
                padding: '40px',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>

                <h1 style={{
                    textAlign: 'center',
                    color: '#333',
                    marginBottom: '10px',
                    fontSize: '28px'
                }}>
                    🎁 FreeMarket
                </h1>

                <p style={{
                    textAlign: 'center',
                    color: '#666',
                    marginBottom: '30px',
                    fontSize: '14px'
                }}>
                    Платформа обмена ресурсами
                </p>

                <form onSubmit={handleSubmit}>
                    <h2 style={{
                        fontSize: '20px',
                        color: '#333',
                        marginBottom: '25px',
                        textAlign: 'center'
                    }}>
                        Заполните анкету
                    </h2>

                    {error && (
                        <div style={{
                            backgroundColor: '#ffebee',
                            color: '#c62828',
                            padding: '12px',
                            borderRadius: '4px',
                            marginBottom: '20px',
                            border: '1px solid #ef5350'
                        }}>
                            {error}
                        </div>
                    )}

                    {/* ФИО Field */}
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontSize: '14px',
                            fontWeight: '500',
                            color: '#333'
                        }}>
                            Ваше ФИО
                        </label>
                        <input
                            type="text"
                            placeholder="Иван Иванов"
                            value={formData.fio}
                            onChange={(e) => setFormData({ ...formData, fio: e.target.value })}
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '12px',
                                fontSize: '14px',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                boxSizing: 'border-box',
                                fontFamily: 'Arial'
                            }}
                        />
                    </div>

                    {/* Telegram Field */}
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontSize: '14px',
                            fontWeight: '500',
                            color: '#333'
                        }}>
                            Телеграм контакт
                        </label>
                        <input
                            type="text"
                            placeholder="@myusername"
                            value={formData.telegram}
                            onChange={(e) => setFormData({ ...formData, telegram: e.target.value })}
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '12px',
                                fontSize: '14px',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                boxSizing: 'border-box',
                                fontFamily: 'Arial'
                            }}
                        />
                        <small style={{ color: '#999', display: 'block', marginTop: '4px' }}>
                            Ваш контакт из Телеграма (@username)
                        </small>
                    </div>

                    {/* Cities Selection */}
                    <div style={{ marginBottom: '25px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '12px',
                            fontSize: '14px',
                            fontWeight: '500',
                            color: '#333'
                        }}>
                            Выберите города (можно несколько)
                        </label>
                        <div style={{
                            backgroundColor: '#f9f9f9',
                            padding: '15px',
                            borderRadius: '4px',
                            border: '1px solid #eee'
                        }}>
                            {CITIES.map(city => (
                                <div key={city} style={{
                                    marginBottom: '10px',
                                    display: 'flex',
                                    alignItems: 'center'
                                }}>
                                    <input
                                        type="checkbox"
                                        id={city}
                                        checked={formData.locations.includes(city)}
                                        onChange={() => handleLocationChange(city)}
                                        disabled={loading}
                                        style={{
                                            marginRight: '10px',
                                            width: '18px',
                                            height: '18px',
                                            cursor: 'pointer'
                                        }}
                                    />
                                    <label
                                        htmlFor={city}
                                        style={{
                                            cursor: 'pointer',
                                            fontSize: '14px',
                                            color: '#333',
                                            flex: 1
                                        }}
                                    >
                                        {city}
                                    </label>
                                </div>
                            ))}
                        </div>
                        {formData.locations.length > 0 && (
                            <small style={{ color: '#666', display: 'block', marginTop: '8px' }}>
                                ✓ Выбрано: {formData.locations.join(', ')}
                            </small>
                        )}
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            width: '100%',
                            padding: '14px',
                            fontSize: '16px',
                            fontWeight: '600',
                            backgroundColor: loading ? '#bbb' : '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => {
                            if (!loading) e.target.style.backgroundColor = '#0056b3';
                        }}
                        onMouseLeave={(e) => {
                            if (!loading) e.target.style.backgroundColor = '#007bff';
                        }}
                    >
                        {loading ? '⏳ Отправка...' : '✓ Отправить анкету'}
                    </button>
                </form>

                <p style={{
                    textAlign: 'center',
                    fontSize: '12px',
                    color: '#999',
                    marginTop: '20px'
                }}>
                    Ваши данные используются только для связи и уведомлений
                </p>
            </div>
        </div>
    );
}
