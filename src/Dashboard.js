import { useEffect, useState } from 'react';
import { getOffers, getUserMatches, getUserProfiles, getUserRatings, getWants, submitRating } from './api';
import './Dashboard.css';

function Dashboard() {
    const [wants, setWants] = useState([]);
    const [offers, setOffers] = useState([]);
    const [profiles, setProfiles] = useState([]);
    const [matches, setMatches] = useState([]);
    const [ratings, setRatings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [userId, setUserId] = useState(1); // Placeholder, should come from auth

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [profilesData, matchesData, ratingsData] = await Promise.all([
                    getUserProfiles(userId),
                    getUserMatches(userId),
                    getUserRatings(userId)
                ]);
                setProfiles(profilesData);
                setMatches(matchesData);
                setRatings(ratingsData);

                // Загрузить wants и offers
                const [wantsData, offersData] = await Promise.all([
                    getWants(),
                    getOffers()
                ]);
                setWants(wantsData);
                setOffers(offersData);
            } catch (err) {
                setError('Ошибка загрузки данных');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [userId]);

    const handleRatingSubmit = async (matchId, score) => {
        try {
            await submitRating({ matchId, score });
            // Refresh ratings
            const updatedRatings = await getUserRatings(userId);
            setRatings(updatedRatings);
        } catch (err) {
            alert('Ошибка отправки оценки');
        }
    };

    if (loading) return <div>Загрузка...</div>;
    if (error) return <div>{error}</div>;

    return (
        <div className="dashboard">
            <h1>Личный кабинет</h1>

            <section>
                <h2>Все wants</h2>
                {wants.length === 0 ? (
                    <p>Нет wants</p>
                ) : (
                    wants.map(item => (
                        <div key={item.id} className="want-card">
                            <h3>{item.title}</h3>
                            <p>{item.description}</p>
                            <p>Категория: {item.category_id}</p>
                            <p>Пользователь: {item.user_id}</p>
                        </div>
                    ))
                )}
            </section>

            <section>
                <h2>Все offers</h2>
                {offers.length === 0 ? (
                    <p>Нет offers</p>
                ) : (
                    offers.map(item => (
                        <div key={item.id} className="offer-card">
                            <h3>{item.title}</h3>
                            <p>{item.description}</p>
                            <p>Категория: {item.category_id}</p>
                            <p>Пользователь: {item.user_id}</p>
                        </div>
                    ))
                )}
            </section>

            <section>
                <h2>Мои анкеты</h2>
                {profiles.length === 0 ? (
                    <p>Нет анкет</p>
                ) : (
                    profiles.map(profile => (
                        <div key={profile.id} className="profile-card">
                            <h3>{profile.name}</h3>
                            <p>Telegram: {profile.telegram}</p>
                            <div>
                                <h4>Ресурсы:</h4>
                                <ul>
                                    {Object.entries(profile.resources).map(([key, value]) => (
                                        <li key={key}>{key}: {value}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    ))
                )}
            </section>

            <section>
                <h2>Совпадения</h2>
                {matches.length === 0 ? (
                    <p>Нет совпадений</p>
                ) : (
                    matches.map(match => (
                        <div key={match.id} className="match-card">
                            <h3>Совпадение с {match.partnerName}</h3>
                            <p>Категория: {match.category}</p>
                            <p>Описание: {match.description}</p>
                            <p>Контакт: {match.contact}</p>
                            <p>Рейтинг: {match.rating} ({match.ratingCount} оценок)</p>
                            <button onClick={() => handleRatingSubmit(match.id, 5)}>Оценить 5 звезд</button>
                            {/* Add more rating options */}
                        </div>
                    ))
                )}
            </section>

            <section>
                <h2>Мои рейтинги</h2>
                {ratings.length === 0 ? (
                    <p>Нет рейтингов</p>
                ) : (
                    ratings.map(rating => (
                        <div key={rating.id} className="rating-card">
                            <p>Оценка: {rating.score}/5</p>
                            <p>Комментарий: {rating.comment}</p>
                            <p>Дата: {new Date(rating.created_at).toLocaleDateString()}</p>
                        </div>
                    ))
                )}
            </section>
        </div>
    );
}

export default Dashboard;
