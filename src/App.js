import { useState } from 'react';
import './App.css';

function App() {
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

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Form submitted:', formData);
        alert('Form submitted!');
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c!</h1>
                <p>\u0417\u0434\u0435\u0441\u044c \u0432\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u043e\u0431\u043c\u0435\u043d\u0438\u0432\u0430\u0442\u044c\u0441\u044f \u0440\u0435\u0441\u0443\u0440\u0441\u0430\u043c\u0438 \u0441 \u0434\u0440\u0443\u0433\u0438\u043c\u0438 \u043b\u044e\u0434\u044c\u043c\u0438 \u0432 \u0433\u043e\u0440\u043e\u0434\u0435 \u0410\u043b\u043c\u0430\u0442\u044b. \u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u043a\u043e\u0440\u043e\u0442\u043a\u0443\u044e \u0430\u043d\u043a\u0435\u0442\u0443 \u0438 \u043e\u0431\u043c\u0435\u043d\u0438\u0432\u0430\u0439\u0442\u0435\u0441\u044c \u0432\u0441\u0435\u043c, \u0447\u0442\u043e \u0432\u0430\u043c \u043d\u0443\u0436\u043d\u043e!</p>
            </header>
            <form onSubmit={handleSubmit} className="form">
                <label>
                    \u0424\u0418\u041e:
                    <input type="text" name="name" value={formData.name} onChange={handleChange} required />
                </label>
                <label>
                    \u041a\u043e\u043d\u0442\u0430\u043a\u0442 \u0432 Telegram:
                    <input type="text" name="telegram" value={formData.telegram} onChange={handleChange} required />
                </label>
                <h2>\u0420\u0435\u0441\u0443\u0440\u0441\u044b</h2>
                <label>
                    \u0414\u0435\u043d\u044c\u0433\u0438 \u0432 \u0430\u0440\u0435\u043d\u0434\u0443:
                    <input type="text" name="money" value={formData.resources.money} onChange={handleChange} />
                </label>
                <label>
                    \u0422\u0435\u0445\u043d\u0438\u043a\u0430:
                    <input type="text" name="tech" value={formData.resources.tech} onChange={handleChange} />
                </label>
                <label>
                    \u041e\u0434\u0435\u0436\u0434\u0430:
                    <input type="text" name="clothes" value={formData.resources.clothes} onChange={handleChange} />
                </label>
                <label>
                    \u0422\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442:
                    <input type="text" name="transport" value={formData.resources.transport} onChange={handleChange} />
                </label>
                <label>
                    \u0415\u0434\u0430:
                    <input type="text" name="food" value={formData.resources.food} onChange={handleChange} />
                </label>
                <label>
                    \u0412\u044b\u0447\u0438\u0441\u043b\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043c\u043e\u0449\u043d\u043e\u0441\u0442\u0438:
                    <input type="text" name="compute" value={formData.resources.compute} onChange={handleChange} />
                </label>
                <label>
                    \u0423\u0441\u043b\u0443\u0433\u0438:
                    <input type="text" name="services" value={formData.resources.services} onChange={handleChange} />
                </label>
                <label>
                    \u0418\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442\u044b:
                    <input type="text" name="tools" value={formData.resources.tools} onChange={handleChange} />
                </label>
                <label>
                    \u041f\u0440\u043e\u0447\u0435\u0435:
                    <input type="text" name="other" value={formData.resources.other} onChange={handleChange} />
                </label>
                <button type="submit">\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c</button>
            </form>
            <footer>
                <p>\u0412\u0430\u0436\u043d\u043e: \u0434\u0435\u043d\u044c\u0433\u0438 \u043f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u043b\u044f\u044e\u0442\u0441\u044f \u0432 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u0435 \u0432\u043e\u0437\u0432\u0440\u0430\u0442\u043d\u043e\u0433\u043e \u043a\u0440\u0435\u0434\u0438\u0442\u0430 \u043f\u043e\u0434 0 %. \u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440, \u0432\u044b \u043c\u0435\u043d\u044f\u0435\u0442\u0435 \u0432\u0435\u043b\u043e\u0441\u0438\u043f\u0435\u0434 \u043d\u0430 n-\u0441\u0443\u043c\u043c\u0443 \u043d\u0430 \u043c\u0435\u0441\u044f\u0446. \u0412 \u043a\u043e\u043d\u0446\u0435 \u043c\u0435\u0441\u044f\u0446\u0430 \u0432\u044b \u043e\u0442\u0434\u0430\u0451\u0442\u0435 \u043e\u0431\u0440\u0430\u0442\u043d\u043e \u0442\u0443 \u0436\u0435 \u0441\u0443\u043c\u043c\u0443, \u0430 \u0432\u0430\u0448 \u043f\u0430\u0440\u0442\u043d\u0451\u0440 \u2014 \u0432\u0435\u043b\u043e\u0441\u0438\u043f\u0435\u0434 \u0432 \u0438\u0437\u043d\u0430\u0447\u0430\u043b\u044c\u043d\u043e\u043c \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0438.</p>
            </footer>
        </div>
    );
}

export default App;
