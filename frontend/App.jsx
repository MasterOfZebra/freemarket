import { useState, useEffect } from 'react';
import ExchangeTabs from './components/ExchangeTabs';
import UserCabinet from './components/UserCabinet';
import LoginModal from './components/LoginModal';
import './styles/App.css';

function App() {
    const [showRegistration, setShowRegistration] = useState(false);
    const [matchesFound, setMatchesFound] = useState(0);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [user, setUser] = useState(null);
    const [showLogin, setShowLogin] = useState(false);
    const [showCabinet, setShowCabinet] = useState(false);
    const [error, setError] = useState(null);

    // Check if user is logged in on app start
    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            const response = await fetch('/auth/me', {
                credentials: 'include'
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
                setIsLoggedIn(true);
            }
        } catch (error) {
            // User not logged in
        }
    };

    const handleLogin = (userData) => {
        setUser(userData);
        setIsLoggedIn(true);
        setShowLogin(false);
    };

    const handleLogout = async () => {
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
        setUser(null);
        setIsLoggedIn(false);
        setShowCabinet(false);
    };

    const handleMatchesFound = (count) => {
        setMatchesFound(count);
    };

    if (showRegistration) {
        return (
            <div className="App">
                <header className="App-header">
                    <h1>🌍 FreeMarket - Платформа обмена ресурсами</h1>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <button
                            onClick={() => setShowRegistration(false)}
                            style={{
                                padding: '12px 30px',
                                marginTop: '15px',
                                backgroundColor: '#666',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '16px',
                                fontWeight: 'bold'
                            }}
                        >
                            ← Назад к спискам
                        </button>
                        {isLoggedIn ? (
                            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                <span style={{ color: 'white', fontSize: '14px' }}>
                                    Привет, {user?.full_name || user?.username || 'Пользователь'}!
                                </span>
                                <button
                                    onClick={() => setShowCabinet(true)}
                                    style={{
                                        padding: '8px 16px',
                                        marginTop: '15px',
                                        backgroundColor: '#4CAF50',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        fontSize: '14px'
                                    }}
                                >
                                    Личный кабинет
                                </button>
                                <button
                                    onClick={handleLogout}
                                    style={{
                                        padding: '8px 16px',
                                        marginTop: '15px',
                                        backgroundColor: '#f44336',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        fontSize: '14px'
                                    }}
                                >
                                    Выйти
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={() => setShowLogin(true)}
                                style={{
                                    padding: '12px 30px',
                                    marginTop: '15px',
                                    backgroundColor: '#2196F3',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '16px',
                                    fontWeight: 'bold'
                                }}
                            >
                                Войти
                            </button>
                        )}
                    </div>
                <ExchangeTabs
                    userId={1}
                    onMatchesFound={handleMatchesFound}
                />
                </header>
            </div>
        );
    }

    return (
        <div className="App">
            <header className="App-header">
                <h1>🌍 FreeMarket - Платформа обмена ресурсами</h1>
                <p>Город Алматы - обменивайтесь всем, что нужно!</p>

                {/* Auth buttons */}
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '15px' }}>
                    {isLoggedIn ? (
                        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                            <span style={{ color: 'white', fontSize: '14px' }}>
                                Привет, {user?.full_name || user?.username || 'Пользователь'}!
                            </span>
                            <button
                                onClick={() => setShowCabinet(true)}
                                style={{
                                    padding: '8px 16px',
                                    backgroundColor: '#4CAF50',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                Личный кабинет
                            </button>
                            <button
                                onClick={handleLogout}
                                style={{
                                    padding: '8px 16px',
                                    backgroundColor: '#f44336',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                Выйти
                            </button>
                        </div>
                    ) : (
                        <button
                            onClick={() => setShowLogin(true)}
                            style={{
                                padding: '8px 16px',
                                backgroundColor: '#2196F3',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            Войти / Регистрация
                        </button>
                    )}
                </div>

                <button
                    onClick={() => setShowRegistration(true)}
                    style={{
                        padding: '12px 30px',
                        marginTop: '15px',
                        backgroundColor: '#ff9800',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}
                >
                    ✏️ Заполнить анкету обмена
                </button>
                {matchesFound > 0 && (
                    <div style={{
                        marginTop: '15px',
                        padding: '10px 20px',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        borderRadius: '6px',
                        fontSize: '14px'
                    }}>
                        ✅ Найдено совпадений: {matchesFound}
                    </div>
                )}
            </header>

            {error && (
                <div style={{ color: 'red', padding: '10px', margin: '10px', textAlign: 'center' }}>
                    Ошибка: {error}
                </div>
            )}

            {/* Убраны ненужные вкладки - пользователи получают данные о партнерах через Telegram */}

            {/* Login Modal */}
            {showLogin && (
                <LoginModal
                    onClose={() => setShowLogin(false)}
                    onLogin={handleLogin}
                />
            )}

            {/* User Cabinet Modal */}
            {showCabinet && (
                <UserCabinet
                    user={user}
                    onClose={() => setShowCabinet(false)}
                    onLogout={handleLogout}
                />
            )}
        </div>
    );
}

export default App;
