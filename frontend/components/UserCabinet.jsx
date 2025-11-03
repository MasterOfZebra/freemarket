import { useState, useEffect } from 'react';

export default function UserCabinet({ user, onClose, onLogout }) {
    const [cabinetData, setCabinetData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState('profile');

    useEffect(() => {
        loadCabinetData();
    }, []);

    const loadCabinetData = async () => {
        try {
            setLoading(true);
            const response = await fetch('/user/cabinet', {
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Не удалось загрузить данные кабинета');
            }

            const data = await response.json();
            setCabinetData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
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
                    textAlign: 'center'
                }}>
                    Загрузка...
                </div>
            </div>
        );
    }

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
                width: '800px',
                maxWidth: '95vw',
                maxHeight: '90vh',
                overflow: 'auto'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h2>Личный кабинет</h2>
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

                {error && (
                    <div style={{
                        color: 'red',
                        marginBottom: '20px',
                        padding: '10px',
                        backgroundColor: '#ffebee',
                        borderRadius: '4px'
                    }}>
                        {error}
                    </div>
                )}

                {/* Tab Navigation */}
                <div style={{ display: 'flex', gap: '5px', marginBottom: '20px', borderBottom: '1px solid #ddd' }}>
                    {[
                        { id: 'profile', label: 'Профиль' },
                        { id: 'listings', label: 'Мои объявления' },
                        { id: 'exchanges', label: 'Обмены' }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            style={{
                                padding: '10px 20px',
                                backgroundColor: activeTab === tab.id ? '#2196F3' : '#f5f5f5',
                                color: activeTab === tab.id ? 'white' : '#333',
                                border: 'none',
                                borderRadius: '4px 4px 0 0',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                {activeTab === 'profile' && (
                    <div>
                        <h3>Профиль пользователя</h3>
                        {cabinetData?.profile && (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>ФИО:</label>
                                    <div style={{ padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                                        {cabinetData.profile.full_name || 'Не указано'}
                                    </div>
                                </div>

                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Username:</label>
                                    <div style={{ padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                                        {cabinetData.profile.username || 'Не указано'}
                                    </div>
                                </div>

                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Email:</label>
                                    <div style={{ padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                                        {cabinetData.profile.email || 'Не указано'}
                                    </div>
                                </div>

                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Телефон:</label>
                                    <div style={{ padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                                        {cabinetData.profile.phone || 'Не указано'}
                                    </div>
                                </div>

                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Telegram:</label>
                                    <div style={{ padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                                        {cabinetData.profile.telegram_contact || 'Не указано'}
                                    </div>
                                </div>

                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Город:</label>
                                    <div style={{ padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                                        {cabinetData.profile.city}
                                    </div>
                                </div>

                                <div style={{ gridColumn: 'span 2' }}>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Рейтинг:</label>
                                    <div style={{ padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                                        ⭐ {cabinetData.profile.rating_avg?.toFixed(1) || '0.0'} (всего обменов: {cabinetData.profile.exchange_count})
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'listings' && (
                    <div>
                        <h3>Мои объявления</h3>
                        {cabinetData?.my_listings?.length > 0 ? (
                            <div style={{ display: 'grid', gap: '15px' }}>
                                {cabinetData.my_listings.map(listing => (
                                    <div key={listing.id} style={{
                                        border: '1px solid #ddd',
                                        borderRadius: '8px',
                                        padding: '15px',
                                        backgroundColor: '#fafafa'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                            <div>
                                                <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>
                                                    {listing.title || `Объявление #${listing.id}`}
                                                </h4>
                                                <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
                                                    {listing.description || 'Без описания'}
                                                </p>
                                                <div style={{ display: 'flex', gap: '15px', fontSize: '12px', color: '#888' }}>
                                                    <span>Хочу: {listing.total_wants}</span>
                                                    <span>Предлагаю: {listing.total_offers}</span>
                                                    <span>Типы: {listing.exchange_types.join(', ')}</span>
                                                </div>
                                            </div>
                                            <div style={{ fontSize: '12px', color: '#666', textAlign: 'right' }}>
                                                {new Date(listing.created_at).toLocaleDateString('ru-RU')}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
                                У вас пока нет объявлений
                            </p>
                        )}
                    </div>
                )}

                {activeTab === 'exchanges' && (
                    <div>
                        <h3>Активные обмены</h3>
                        {cabinetData?.active_exchanges?.length > 0 ? (
                            <div style={{ display: 'grid', gap: '15px' }}>
                                {cabinetData.active_exchanges.map(exchange => (
                                    <div key={exchange.id} style={{
                                        border: '1px solid #ddd',
                                        borderRadius: '8px',
                                        padding: '15px',
                                        backgroundColor: '#fafafa'
                                    }}>
                                        <p>Обмен #{exchange.id} - {exchange.status}</p>
                                        <p>Тип: {exchange.exchange_type}, Сумма: {exchange.value_tenge}₸</p>
                                        <p>Категория: {exchange.category}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
                                Активных обменов пока нет
                            </p>
                        )}
                    </div>
                )}

                <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '1px solid #ddd', textAlign: 'center' }}>
                    <button
                        onClick={onLogout}
                        style={{
                            padding: '10px 20px',
                            backgroundColor: '#f44336',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '14px'
                        }}
                    >
                        Выйти из аккаунта
                    </button>
                </div>
            </div>
        </div>
    );
}
