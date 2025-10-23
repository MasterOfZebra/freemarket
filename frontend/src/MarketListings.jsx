import { useEffect, useState } from 'react';
import { getOffers, getWants } from './api';

export default function MarketListings() {
    const [wants, setWants] = useState([]);
    const [offers, setOffers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let mounted = true;
        Promise.all([getWants(), getOffers()])
            .then(([wResp, oResp]) => {
                if (!mounted) return;
                setWants(wResp.listings || []);
                setOffers(oResp.listings || []);
            })
            .catch((e) => setError(e.message || 'Failed to load'))
            .finally(() => mounted && setLoading(false));
        return () => (mounted = false);
    }, []);

    if (loading) return <div>Загрузка рыночных объявлений...</div>;
    if (error) return <div>Ошибка: {error}</div>;

    return (
        <div style={{ padding: '1rem' }}>
            <h2>Хочу (Wants)</h2>
            {wants.length === 0 ? <p>Пусто</p> : (
                <ul>
                    {wants.map((l) => (
                        <li key={l.id}>{l.title} — {l.description || ''}</li>
                    ))}
                </ul>
            )}

            <h2>Дарю / Отдаю (Offers)</h2>
            {offers.length === 0 ? <p>Пусто</p> : (
                <ul>
                    {offers.map((l) => (
                        <li key={l.id}>{l.title} — {l.description || ''}</li>
                    ))}
                </ul>
            )}
        </div>
    );
}
