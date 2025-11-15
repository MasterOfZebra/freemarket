import { useState } from 'react';

export default function LoginModal({ onClose, onLogin }) {
    const [isRegister, setIsRegister] = useState(false);
    const [formData, setFormData] = useState({
        identifier: '', // email, phone, or username for login
        email: '',
        phone: '',
        username: '',
        password: '',
        full_name: '',
        telegram_contact: '',
        city: 'Алматы'
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleInputChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const endpoint = isRegister ? '/auth/register' : '/auth/login';

            let response;
            if (isRegister) {
                // Registration uses JSON
                const payload = {
                    email: formData.email || null,
                    phone: formData.phone || null,
                    username: formData.username || null,
                    password: formData.password,
                    full_name: formData.full_name,
                    telegram_contact: formData.telegram_contact || null,
                    city: formData.city
                };
                response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
            } else {
                // Login uses form-urlencoded
                const formDataObj = new URLSearchParams();
                if (formData.identifier.includes('@')) {
                    formDataObj.append('email', formData.identifier);
                } else {
                    formDataObj.append('identifier', formData.identifier);
                }
                formDataObj.append('password', formData.password);

                response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    credentials: 'include',
                    body: formDataObj.toString()
                });
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Ошибка авторизации');
            }

            // Both registration and login now return LoginResponse with access_token
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
            }

            if (isRegister) {
                // After registration, automatically log in the user
                onLogin({ ...data.user, access_token: data.access_token });
            } else {
                // Login successful - save access token and user data
                onLogin({ ...data.user, access_token: data.access_token });
            }

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
        }}>
            <div style={{
                backgroundColor: 'white',
                padding: '30px',
                borderRadius: '8px',
                width: '400px',
                maxWidth: '90vw',
                maxHeight: '90vh',
                overflow: 'auto'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h2>{isRegister ? 'Регистрация' : 'Вход'}</h2>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '24px',
                            cursor: 'pointer',
                            color: '#666'
                        }}
                    >
                        ×
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    {isRegister ? (
                        // Registration form
                        <>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                    ФИО *
                                </label>
                                <input
                                    type="text"
                                    value={formData.full_name}
                                    onChange={(e) => handleInputChange('full_name', e.target.value)}
                                    placeholder="Ваше полное имя"
                                    required
                                    style={{
                                        width: '100%',
                                        padding: '8px',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>

                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                    Email или Телефон *
                                </label>
                                <input
                                    type="text"
                                    value={formData.email || formData.phone}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        // Simple check if it's email or phone
                                        if (value.includes('@')) {
                                            handleInputChange('email', value);
                                            handleInputChange('phone', '');
                                        } else {
                                            handleInputChange('phone', value);
                                            handleInputChange('email', '');
                                        }
                                    }}
                                    placeholder="email@example.com или +7..."
                                    required
                                    style={{
                                        width: '100%',
                                        padding: '8px',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>

                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                    Username (опционально)
                                </label>
                                <input
                                    type="text"
                                    value={formData.username}
                                    onChange={(e) => handleInputChange('username', e.target.value)}
                                    placeholder="username"
                                    style={{
                                        width: '100%',
                                        padding: '8px',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>

                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                    Telegram (опционально)
                                </label>
                                <input
                                    type="text"
                                    value={formData.telegram_contact}
                                    onChange={(e) => handleInputChange('telegram_contact', e.target.value)}
                                    placeholder="@username"
                                    style={{
                                        width: '100%',
                                        padding: '8px',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>
                        </>
                    ) : (
                        // Login form
                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Email, телефон или username
                            </label>
                            <input
                                type="text"
                                value={formData.identifier}
                                onChange={(e) => handleInputChange('identifier', e.target.value)}
                                placeholder="email@example.com, +7... или username"
                                required
                                style={{
                                    width: '100%',
                                    padding: '8px',
                                    border: '1px solid #ddd',
                                    borderRadius: '4px',
                                    fontSize: '14px'
                                }}
                            />
                        </div>
                    )}

                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                            Пароль *
                        </label>
                        <input
                            type="password"
                            value={formData.password}
                            onChange={(e) => handleInputChange('password', e.target.value)}
                            placeholder="Минимум 8 символов"
                            required
                            minLength={8}
                            style={{
                                width: '100%',
                                padding: '8px',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                fontSize: '14px'
                            }}
                        />
                    </div>

                    {error && (
                        <div style={{
                            color: 'red',
                            marginBottom: '15px',
                            padding: '10px',
                            backgroundColor: '#ffebee',
                            borderRadius: '4px',
                            fontSize: '14px'
                        }}>
                            {error}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                flex: 1,
                                padding: '10px',
                                backgroundColor: '#4CAF50',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                fontSize: '16px',
                                fontWeight: 'bold'
                            }}
                        >
                            {loading ? 'Загрузка...' : (isRegister ? 'Зарегистрироваться' : 'Войти')}
                        </button>
                    </div>

                    <div style={{ textAlign: 'center' }}>
                        <button
                            type="button"
                            onClick={() => setIsRegister(!isRegister)}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: '#2196F3',
                                cursor: 'pointer',
                                textDecoration: 'underline'
                            }}
                        >
                            {isRegister ? 'Уже есть аккаунт? Войти' : 'Нет аккаунта? Зарегистрироваться'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
