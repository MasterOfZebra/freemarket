import { useEffect, useState } from 'react';
import { getOffers, getWants } from './services/api';
import './styles/App.css';

function App() {
    const [wants, setWants] = useState([]);
    const [offers, setOffers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('wants');
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        user_id: 1,
        listing_type: 'want',
        title: '',
        description: '',
        category: '',
        location: ''
    });

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

    const handleFormSubmit = async (e) => {
        e.preventDefault();
        try {
            // TODO: Send form data to backend API
            console.log('Form submitted:', formData);
            setShowForm(false);
            // Reset form
            setFormData({
                user_id: 1,
                listing_type: 'want',
                title: '',
                description: '',
                category: '',
                location: ''
            });
        } catch (err) {
            console.error('Error submitting form:', err);
        }
    };

    const handleFormChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    if (loading) {
        return <div style={{ padding: '20px', textAlign: 'center' }}>Загрузка...</div>;
    }

    return (
        <div className="App">
            <header className="App-header">
                <h1>Добро пожаловать на FreeMarket!</h1>
                <p>Платформа обмена ресурсами в городе Алматы</p>
                <button
                    onClick={() => setShowForm(!showForm)}
                    style={{
                        padding: '10px 20px',
                        marginTop: '10px',
                        backgroundColor: '#ff9800',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '16px'
                    }}
                >
                    {showForm ? 'Закрыть анкету' : 'Создать объявление'}
                </button>
            </header>

            {showForm && (
                <div style={{ 
                    padding: '20px', 
                    backgroundColor: '#f5f5f5', 
                    margin: '20px',
                    borderRadius: '4px',
                    border: '2px solid #ff9800'
                }}>
                    <h2>Создать новое объявление</h2>
                    <form onSubmit={handleFormSubmit}>
                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Тип объявления *
                            </label>
                            <select
                                name="listing_type"
                                value={formData.listing_type}
                                onChange={handleFormChange}
                                required
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd'
                                }}
                            >
                                <option value="want">Хочу (Want)</option>
                                <option value="offer">Могу (Offer)</option>
                            </select>
                        </div>

                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Название *
                            </label>
                            <input
                                type="text"
                                name="title"
                                value={formData.title}
                                onChange={handleFormChange}
                                placeholder="Введите название объявления"
                                required
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd',
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Описание *
                            </label>
                            <textarea
                                name="description"
                                value={formData.description}
                                onChange={handleFormChange}
                                placeholder="Подробное описание"
                                required
                                rows="4"
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd',
                                    boxSizing: 'border-box',
                                    fontFamily: 'Arial, sans-serif'
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Категория *
                            </label>
                            <input
                                type="text"
                                name="category"
                                value={formData.category}
                                onChange={handleFormChange}
                                placeholder="Например: электроника, мебель, услуги"
                                required
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd',
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Локация *
                            </label>
                            <input
                                type="text"
                                name="location"
                                value={formData.location}
                                onChange={handleFormChange}
                                placeholder="Район или адрес в Алматы"
                                required
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd',
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <button
                            type="submit"
                            style={{
                                padding: '12px 24px',
                                backgroundColor: '#4CAF50',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '16px',
                                marginRight: '10px'
                            }}
                        >
                            Опубликовать
                        </button>
                        <button
                            type="button"
                            onClick={() => setShowForm(false)}
                            style={{
                                padding: '12px 24px',
                                backgroundColor: '#f44336',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '16px'
                            }}
                        >
                            Отмена
                        </button>
                    </form>
                </div>
            )}

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
