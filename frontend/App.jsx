import { useEffect, useState } from 'react';
import { getOffers, getWants } from './services/api';
import ExchangeTabs from './components/ExchangeTabs';
import './styles/App.css';

function App() {
    const [wants, setWants] = useState([]);
    const [offers, setOffers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('wants');
    const [showRegistration, setShowRegistration] = useState(false);
    const [matchesFound, setMatchesFound] = useState(0);

    const fetchData = async () => {
        try {
            const [wantsData, offersData] = await Promise.all([
                getWants(),
                getOffers()
            ]);
            setWants(wantsData);
            setOffers(offersData);
        } catch (err) {
            setError('Ошибка загрузки данных: ' + err.message);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleMatchesFound = (count: number) => {
        setMatchesFound(count);
        // Refresh listings after successful registration
        setTimeout(() => {
            fetchData();
        }, 2000);
    };

    if (loading && !showRegistration) {
        return <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка...</div>;
    }

    if (showRegistration) {
        return (
            <div className="App">
                <header className="App-header">
                    <h1>🌍 FreeMarket - Платформа обмена ресурсами</h1>
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
                </header>
                <ExchangeTabs 
                    userId={1} 
                    onMatchesFound={handleMatchesFound}
                />
            </div>
        );
    }

    return (
        <div className="App">
            <header className="App-header">
                <h1>🌍 FreeMarket - Платформа обмена ресурсами</h1>
                <p>Город Алматы - обменивайтесь всем, что нужно!</p>
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

            <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
                <div style={{
                    display: 'flex',
                    gap: '10px',
                    marginBottom: '20px',
                    borderBottom: '3px solid #ddd'
                }}>
                    <button
                        onClick={() => setActiveTab('wants')}
                        style={{
                            padding: '12px 24px',
                            backgroundColor: activeTab === 'wants' ? '#007bff' : '#eee',
                            color: activeTab === 'wants' ? 'white' : '#333',
                            border: 'none',
                            borderRadius: '4px 4px 0 0',
                            cursor: 'pointer',
                            fontSize: '16px',
                            fontWeight: 'bold'
                        }}
                    >
                        🔵 НУЖНО (Wants) - {wants.length}
                    </button>
                    <button
                        onClick={() => setActiveTab('offers')}
                        style={{
                            padding: '12px 24px',
                            backgroundColor: activeTab === 'offers' ? '#28a745' : '#eee',
                            color: activeTab === 'offers' ? 'white' : '#333',
                            border: 'none',
                            borderRadius: '4px 4px 0 0',
                            cursor: 'pointer',
                            fontSize: '16px',
                            fontWeight: 'bold'
                        }}
                    >
                        🟢 ПРЕДЛАГАЮ (Offers) - {offers.length}
                    </button>
                </div>

                {activeTab === 'wants' && (
                    <section>
                        <h2 style={{ color: '#007bff' }}>🔵 Что люди ищут (НУЖНО)</h2>
                        {wants.length === 0 ? (
                            <p style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
                                Нет активных запросов
                            </p>
                        ) : (
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                                gap: '15px'
                            }}>
                                {wants.map(item => (
                                    <div
                                        key={item.id}
                                        style={{
                                            border: '2px solid #007bff',
                                            padding: '15px',
                                            borderRadius: '6px',
                                            backgroundColor: '#f0f7ff',
                                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                        }}
                                    >
                                        <h3 style={{ margin: '0 0 10px 0', color: '#007bff' }}>
                                            {item.title}
                                        </h3>
                                        <p style={{ margin: '5px 0', color: '#555', fontSize: '14px' }}>
                                            {item.description}
                                        </p>
                                        {item.category && (
                                            <p style={{
                                                margin: '8px 0 0 0',
                                                fontSize: '12px',
                                                color: '#999',
                                                padding: '8px',
                                                backgroundColor: 'white',
                                                borderRadius: '4px'
                                            }}>
                                                📁 {item.category}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                )}

                {activeTab === 'offers' && (
                    <section>
                        <h2 style={{ color: '#28a745' }}>🟢 Что люди предлагают (ПРЕДЛАГАЮ)</h2>
                        {offers.length === 0 ? (
                            <p style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
                                Нет активных предложений
                            </p>
                        ) : (
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                                gap: '15px'
                            }}>
                                {offers.map(item => (
                                    <div
                                        key={item.id}
                                        style={{
                                            border: '2px solid #28a745',
                                            padding: '15px',
                                            borderRadius: '6px',
                                            backgroundColor: '#f0fff0',
                                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                        }}
                                    >
                                        <h3 style={{ margin: '0 0 10px 0', color: '#28a745' }}>
                                            {item.title}
                                        </h3>
                                        <p style={{ margin: '5px 0', color: '#555', fontSize: '14px' }}>
                                            {item.description}
                                        </p>
                                        {item.category && (
                                            <p style={{
                                                margin: '8px 0 0 0',
                                                fontSize: '12px',
                                                color: '#999',
                                                padding: '8px',
                                                backgroundColor: 'white',
                                                borderRadius: '4px'
                                            }}>
                                                📁 {item.category}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                )}
            </div>
        </div>
    );
}

export default App;
