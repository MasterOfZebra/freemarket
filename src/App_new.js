import { useState } from 'react';
import { Link, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { submitProfile } from './api';
import './App.css';
import Dashboard from './Dashboard';

function ProfileForm() {
    const [formData, setFormData] = useState({
        name: '',
        telegram: '',
        resources: {
            money: '',
            tech: '',
            clothes: '',
            transport: '',
            food: '',
            compute: '',
            services: '',
            tools: '',
            other: ''
        }
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name in formData.resources) {
            setFormData({
                ...formData,
                resources: {
                    ...formData.resources,
                    [name]: value
                }
            });
        } else {
            setFormData({
                ...formData,
                [name]: value
            });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await submitProfile(formData);
            alert('Анкета отправлена!');
            // Redirect to dashboard or update state
        } catch (error) {
            alert('Ошибка отправки анкеты');
        }
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>Добро пожаловать!</h1>
                <p>Здесь вы можете обмениваться ресурсами с другими людьми в городе Алматы. Заполните короткую анкету и обменивайтесь всем, что вам нужно!</p>
                <Link to="/dashboard">Личный кабинет</Link>
            </header>
            <form onSubmit={handleSubmit} className="form">
                <label>
                    ФИО:
                    <input type="text" name="name" value={formData.name} onChange={handleChange} required />
                </label>
                <label>
                    Контакт в Telegram:
                    <input type="text" name="telegram" value={formData.telegram} onChange={handleChange} required />
                </label>
                <h2>Ресурсы</h2>
                <label>
                    Деньги в аренду:
                    <input type="text" name="money" value={formData.resources.money} onChange={handleChange} />
                </label>
                <label>
                    Техника:
                    <input type="text" name="tech" value={formData.resources.tech} onChange={handleChange} />
                </label>
                <label>
                    Одежда:
                    <input type="text" name="clothes" value={formData.resources.clothes} onChange={handleChange} />
                </label>
                <label>
                    Транспорт:
                    <input type="text" name="transport" value={formData.resources.transport} onChange={handleChange} />
                </label>
                <label>
                    Еда:
                    <input type="text" name="food" value={formData.resources.food} onChange={handleChange} />
                </label>
                <label>
                    Вычислительные мощности:
                    <input type="text" name="compute" value={formData.resources.compute} onChange={handleChange} />
                </label>
                <label>
                    Услуги:
                    <input type="text" name="services" value={formData.resources.services} onChange={handleChange} />
                </label>
                <label>
                    Инструменты:
                    <input type="text" name="tools" value={formData.resources.tools} onChange={handleChange} />
                </label>
                <label>
                    Прочее:
                    <input type="text" name="other" value={formData.resources.other} onChange={handleChange} />
                </label>
                <button type="submit">Отправить</button>
            </form>
            <footer>
                <p>Важно: деньги предоставляются в качестве возвратного кредита под 0 %. Например, вы меняете велосипед на сумму на месяц. В конце месяца вы отдаёте обратно ту же сумму, а ваш партнёр — велосипед в изначальном состоянии.</p>
            </footer>
        </div>
    );
}

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<ProfileForm />} />
                <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
        </Router>
    );
}

export default App;
