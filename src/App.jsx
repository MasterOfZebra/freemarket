import { useState, useEffect } from 'react';
import { getWants, getOffers } from './api';
import './App.css';

function App() {
    const [wants, setWants] = useState([]);
    const [offers, setOffers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('wants');

    useEffect(() => {
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
        fetchData();
    }, []);

    if (loading) {
        return <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка...</div>;
    }

    return (
        <div className="App">
            <header className="App-header">
                <h1>Добро пожаловать на FreeMarket!</h1>
                <p>Платформа обмена ресурсами в городе Алматы</p>
            </header>

            {error && (
                <div style={{ color: 'red', padding: '10px', margin: '10px' }}>
                    Ошибка: {error}
                </div>
            )}

            <div style={{ padding: '20px' }}>
                <div style={{ marginBottom: '20px' }}>
                    <button 
                        onClick={() => setActiveTab('wants')}
                        style={{
                            padding: '10px 20px',
                            marginRight: '10px',
                            backgroundColor: activeTab === 'wants' ? '#007bff' : '#ccc',
                            color: activeTab === 'wants' ? 'white' : 'black',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Хочу (Wants) - {wants.length}
                    </button>
                    <button
                        onClick={() => setActiveTab('offers')}
                        style={{
                            padding: '10px 20px',
                            backgroundColor: activeTab === 'offers' ? '#28a745' : '#ccc',
                            color: activeTab === 'offers' ? 'white' : 'black',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Могу (Offers) - {offers.length}
                    </button>
                </div>

                {activeTab === 'wants' && (
                    <section>
                        <h2>Хочу (Wants)</h2>
                        {wants.length === 0 ? (
                            <p>Нет объявлений</p>
                        ) : (
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {wants.map(item => (
                                    <div
                                        key={item.id}
                                        style={{
                                            border: '1px solid #ddd',
                                            padding: '15px',
                                            borderRadius: '4px',
                                            backgroundColor: '#f9f9f9'
                                        }}
                                    >
                                        <h3 style={{ margin: '0 0 10px 0' }}>{item.title}</h3>
                                        <p style={{ margin: '5px 0', color: '#666' }}>{item.description}</p>
                                        <p style={{ margin: '5px 0', fontSize: '12px', color: '#999' }}>
                                            Категория ID: {item.category_id} | Пользователь ID: {item.user_id}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                )}

                {activeTab === 'offers' && (
                    <section>
                        <h2>Могу (Offers)</h2>
                        {offers.length === 0 ? (
                            <p>Нет объявлений</p>
                        ) : (
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {offers.map(item => (
                                    <div
                                        key={item.id}
                                        style={{
                                            border: '1px solid #ddd',
                                            padding: '15px',
                                            borderRadius: '4px',
                                            backgroundColor: '#f0f9f0'
                                        }}
                                    >
                                        <h3 style={{ margin: '0 0 10px 0' }}>{item.title}</h3>
                                        <p style={{ margin: '5px 0', color: '#666' }}>{item.description}</p>
                                        <p style={{ margin: '5px 0', fontSize: '12px', color: '#999' }}>
                                            Категория ID: {item.category_id} | Пользователь ID: {item.user_id}
                                        </p>
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
