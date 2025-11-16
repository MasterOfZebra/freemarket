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
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                return; // No token, user not logged in
            }

            const response = await fetch('/auth/me', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                },
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                // New format: {user: UserProfile | null, authenticated: boolean}
                if (data.authenticated && data.user) {
                    setUser({ ...data.user, access_token: accessToken });
                    setIsLoggedIn(true);
                } else {
                    // Not authenticated, try to refresh token
                    try {
                        const refreshResponse = await fetch('/auth/refresh', {
                            method: 'POST',
                            credentials: 'include'
                        });
                        if (refreshResponse.ok) {
                            const refreshData = await refreshResponse.json();
                            localStorage.setItem('access_token', refreshData.access_token);
                            // Retry /auth/me with new token
                            const retryResponse = await fetch('/auth/me', {
                                headers: {
                                    'Authorization': `Bearer ${refreshData.access_token}`
                                },
                                credentials: 'include'
                            });
                            if (retryResponse.ok) {
                                const retryData = await retryResponse.json();
                                if (retryData.authenticated && retryData.user) {
                                    setUser({ ...retryData.user, access_token: refreshData.access_token });
                                    setIsLoggedIn(true);
                                } else {
                                    localStorage.removeItem('access_token');
                                }
                            } else {
                                localStorage.removeItem('access_token');
                            }
                        } else {
                            // Refresh failed, clear token
                            localStorage.removeItem('access_token');
                        }
                    } catch (refreshError) {
                        localStorage.removeItem('access_token');
                    }
                }
            }
        } catch (error) {
            // User not logged in
            console.error('Auth check error:', error);
        }
    };

    const handleLogin = (userData) => {
        setUser(userData);
        setIsLoggedIn(true);
        setShowLogin(false);
    };

    const handleLogout = async () => {
        try {
            const accessToken = localStorage.getItem('access_token');
            await fetch('/auth/logout', {
                method: 'POST',
                headers: accessToken ? {
                    'Authorization': `Bearer ${accessToken}`
                } : {},
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
        localStorage.removeItem('access_token');
        setUser(null);
        setIsLoggedIn(false);
        setShowCabinet(false);
    };

    const handleMatchesFound = (count) => {
        setMatchesFound(count);
    };

    const handleListingCreated = () => {
        // Trigger cabinet data refresh if cabinet is open
        if (showCabinet) {
            // Force re-render by toggling showCabinet
            setShowCabinet(false);
            setTimeout(() => setShowCabinet(true), 100);
        }
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
                                    type="button"
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
                {isLoggedIn && user?.id ? (
                    <ExchangeTabs
                        userId={user.id}
                        onMatchesFound={handleMatchesFound}
                        onListingCreated={handleListingCreated}
                    />
                ) : (
                    <div style={{
                        padding: '40px',
                        textAlign: 'center',
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: '8px',
                        marginTop: '20px'
                    }}>
                        <p style={{ color: 'white', fontSize: '18px', marginBottom: '20px' }}>
                            Для создания объявления необходимо войти в систему
                        </p>
                        <button
                            onClick={() => setShowLogin(true)}
                            style={{
                                padding: '12px 30px',
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
                    </div>
                )}
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
                                type="button"
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
