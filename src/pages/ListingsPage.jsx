import { useState } from 'react';

const CATEGORIES = [
    { id: 'food', name: 'Продукты', icon: '🍎' },
    { id: 'clothes', name: 'Одежда', icon: '👕' },
    { id: 'tools', name: 'Инструменты', icon: '🔧' },
    { id: 'books', name: 'Книги', icon: '📚' },
    { id: 'furniture', name: 'Мебель', icon: '🪑' },
    { id: 'services', name: 'Услуги', icon: '💼' }
];

export function ListingsPage({ userId, userName, onListingsComplete }) {
    const [descriptions, setDescriptions] = useState({
        wants: {},
        offers: {}
    });
    const [submittedItems, setSubmittedItems] = useState({ wants: [], offers: [] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleDescriptionChange = (type, category, value) => {
        setDescriptions(prev => ({
            ...prev,
            [type]: { ...prev[type], [category]: value }
        }));
    };

    const handleSubmit = async (type, category) => {
        const description = descriptions[type][category];
        if (!description || !description.trim()) {
            setError(`Пожалуйста, заполните описание для ${getCategoryName(category)}`);
            return;
        }

        setError(null);
        setLoading(true);

        try {
            const response = await fetch('/api/market-listings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: parseInt(userId),
                    title: `${type === 'wants' ? 'Ищу' : 'Даю'} ${getCategoryName(category)}`,
                    description: description.trim(),
                    category: category,
                    kind: type === 'wants' ? 2 : 1,
                    active: true
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при добавлении товара');
            }

            const listingData = await response.json();
            console.log(`✅ ${type} listing created:`, listingData);

            setDescriptions(prev => ({
                ...prev,
                [type]: { ...prev[type], [category]: '' }
            }));

            setSubmittedItems(prev => ({
                ...prev,
                [type]: [...new Set([...prev[type], category])]
            }));

            // Brief success message
            const categoryName = getCategoryName(category);
            alert(`✅ "${categoryName}" добавлено!`);
        } catch (err) {
            setError('❌ Ошибка: ' + err.message);
            console.error('Listing submission error:', err);
        } finally {
            setLoading(false);
        }
    };

    const getCategoryName = (id) => CATEGORIES.find(c => c.id === id)?.name || id;

    const CategoryInput = ({ type, category }) => {
        const isSubmitted = submittedItems[type].includes(category);

        return (
            <div style={{
                marginBottom: '20px',
                padding: '15px',
                backgroundColor: type === 'wants' ? '#f0f7ff' : '#f0fff0',
                borderRadius: '4px',
                border: isSubmitted ? '2px solid #28a745' : '1px solid #ddd'
            }}>
                <label style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: '#333',
                    display: 'flex',
                    alignItems: 'center'
                }}>
                    <span style={{ fontSize: '24px', marginRight: '8px' }}>
                        {CATEGORIES.find(c => c.id === category)?.icon}
                    </span>
                    {getCategoryName(category)}
                    {isSubmitted && <span style={{ marginLeft: '8px', color: '#28a745' }}>✓</span>}
                </label>

                <textarea
                    placeholder={`Опишите что вы ${type === 'wants' ? 'ищете' : 'можете дать'} в этой категории...`}
                    value={descriptions[type][category] || ''}
                    onChange={(e) => handleDescriptionChange(type, category, e.target.value)}
                    disabled={loading}
                    style={{
                        width: '100%',
                        height: '80px',
                        padding: '10px',
                        marginTop: '8px',
                        marginBottom: '10px',
                        borderRadius: '4px',
                        border: '1px solid #ddd',
                        fontFamily: 'Arial',
                        fontSize: '13px',
                        resize: 'vertical',
                        boxSizing: 'border-box'
                    }}
                />

                <button
                    onClick={() => handleSubmit(type, category)}
                    disabled={loading || !descriptions[type][category]?.trim()}
                    style={{
                        width: '100%',
                        padding: '10px',
                        backgroundColor: loading ? '#bbb' : (type === 'wants' ? '#007bff' : '#28a745'),
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontWeight: '600',
                        fontSize: '13px'
                    }}
                >
                    {loading ? '⏳ Добавление...' : '+ Добавить'}
                </button>
            </div>
        );
    };

    return (
        <div style={{
            padding: '20px',
            backgroundColor: '#f5f5f5',
            minHeight: '100vh'
        }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto' }}>

                {/* Header */}
                <div style={{
                    backgroundColor: 'white',
                    padding: '20px',
                    borderRadius: '8px',
                    marginBottom: '20px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                    <h1 style={{ margin: '0 0 10px 0', fontSize: '24px', color: '#333' }}>
                        Добавьте свои Хочу и Могу
                    </h1>
                    <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>
                        Добро пожаловать, {userName}!
                        <br />
                        Заполните хотя бы по одному товару в каждой категории для поиска совпадений
                    </p>
                </div>

                {error && (
                    <div style={{
                        backgroundColor: '#ffebee',
                        color: '#c62828',
                        padding: '15px',
                        borderRadius: '4px',
                        marginBottom: '20px',
                        border: '1px solid #ef5350'
                    }}>
                        {error}
                    </div>
                )}

                {/* Two Column Layout */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '20px',
                    marginBottom: '30px'
                }}>

                    {/* LEFT: WANTS */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '20px',
                        borderRadius: '8px',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        border: '2px solid #007bff'
                    }}>
                        <h2 style={{
                            color: '#007bff',
                            fontSize: '22px',
                            marginTop: '0',
                            marginBottom: '15px',
                            display: 'flex',
                            alignItems: 'center'
                        }}>
                            <span style={{ fontSize: '28px', marginRight: '10px' }}>🙏</span>
                            Хочу (WANTS)
                        </h2>
                        <p style={{ color: '#666', marginBottom: '15px', fontSize: '13px' }}>
                            Что вы ищете и нужно вам?
                        </p>

                        {CATEGORIES.map(cat => (
                            <CategoryInput key={cat.id} type="wants" category={cat.id} />
                        ))}
                    </div>

                    {/* RIGHT: OFFERS */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '20px',
                        borderRadius: '8px',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        border: '2px solid #28a745'
                    }}>
                        <h2 style={{
                            color: '#28a745',
                            fontSize: '22px',
                            marginTop: '0',
                            marginBottom: '15px',
                            display: 'flex',
                            alignItems: 'center'
                        }}>
                            <span style={{ fontSize: '28px', marginRight: '10px' }}>💝</span>
                            Могу (OFFERS)
                        </h2>
                        <p style={{ color: '#666', marginBottom: '15px', fontSize: '13px' }}>
                            Что вы можете предложить?
                        </p>

                        {CATEGORIES.map(cat => (
                            <CategoryInput key={cat.id} type="offers" category={cat.id} />
                        ))}
                    </div>

                </div>

                {/* Statistics */}
                <div style={{
                    backgroundColor: 'white',
                    padding: '20px',
                    borderRadius: '8px',
                    marginBottom: '20px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    textAlign: 'center'
                }}>
                    <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>
                        <strong>Статус:</strong>
                        <span style={{ marginLeft: '10px' }}>
                            {submittedItems.wants.length} товаров добавлено в "Хочу"
                            <span style={{ margin: '0 15px' }}>|</span>
                            {submittedItems.offers.length} товаров добавлено в "Могу"
                        </span>
                    </p>
                </div>

                {/* Next Step Button */}
                <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                    <button
                        onClick={onListingsComplete}
                        disabled={submittedItems.wants.length === 0 || submittedItems.offers.length === 0}
                        style={{
                            padding: '15px 40px',
                            fontSize: '16px',
                            fontWeight: '600',
                            backgroundColor: submittedItems.wants.length > 0 && submittedItems.offers.length > 0 ? '#6c757d' : '#ccc',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: submittedItems.wants.length > 0 && submittedItems.offers.length > 0 ? 'pointer' : 'not-allowed'
                        }}
                    >
                        → Найти совпадения
                    </button>
                    <p style={{ fontSize: '12px', color: '#999', marginTop: '10px' }}>
                        Добавьте хотя бы по одному товару в каждой категории
                    </p>
                </div>
            </div>
        </div>
    );
}
