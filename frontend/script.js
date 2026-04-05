const API_BASE = 'http://localhost:5000';

// Проверка здоровья сервера при загрузке
async function checkServerHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        if (data.status === 'healthy') {
            console.log('✅ Сервер работает');
        } else {
            console.warn('⚠️ Сервер не отвечает');
        }
    } catch (error) {
        console.error('❌ Ошибка подключения к серверу:', error);
        alert('Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен на порту 5000');
    }
}

// Проверка номера
document.getElementById('checkBtn').addEventListener('click', async () => {
    const phone = document.getElementById('phoneInput').value;
    const resultDiv = document.getElementById('checkResult');
    
    if (!phone) {
        resultDiv.innerHTML = '<span style="color: red;">❌ Введите номер телефона</span>';
        return;
    }

    resultDiv.innerHTML = '🔄 Проверка номера...';
    
    try {
        const res = await fetch(`${API_BASE}/check_number`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone })
        });
        
        const data = await res.json();
        
        if (data.error) {
            resultDiv.innerHTML = `<span style="color: red;">❌ ${data.error}</span>`;
        } else {
            const riskPercent = (data.risk_score * 100).toFixed(0);
            resultDiv.innerHTML = `
                <div style="font-size: 1.2rem; margin-bottom: 10px;">${data.emoji} ${data.status}</div>
                <div><strong>Риск:</strong> ${riskPercent}%</div>
                <div><strong>Жалоб:</strong> ${data.reports_count}</div>
                ${data.details && data.details.length > 0 ? `<div><strong>Последняя жалоба:</strong> ${data.details[0].city}, ${data.details[0].text.substring(0, 100)}</div>` : ''}
            `;
        }
    } catch (err) {
        resultDiv.innerHTML = '<span style="color: red;">❌ Ошибка соединения с сервером</span>';
        console.error(err);
    }
});

// Анализ аудио
document.getElementById('analyzeBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('audioFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Выберите аудиофайл для анализа');
        return;
    }

    const formData = new FormData();
    formData.append('audio', file);

    const analyzeBtn = document.getElementById('analyzeBtn');
    const originalText = analyzeBtn.textContent;
    analyzeBtn.textContent = '🔄 Анализируем...';
    analyzeBtn.disabled = true;

    document.getElementById('transcript').innerText = '⏳ Обработка...';
    document.getElementById('voiceType').innerText = '⏳ Анализ...';
    document.getElementById('fraudProb').innerText = '⏳ Ожидание...';
    document.getElementById('explanation').innerText = '⏳ Анализ...';

    try {
        const res = await fetch(`${API_BASE}/analyze_audio`, {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('transcript').innerHTML = `<strong>📝 Текст разговора:</strong><br>"${data.transcript}"`;
            document.getElementById('voiceType').innerHTML = `<strong>🎤 Тип голоса:</strong><br>${data.voice_analysis}`;
            
            const fraudData = data.fraud_analysis;
            document.getElementById('fraudProb').innerHTML = `<strong>⚠️ Вероятность мошенничества:</strong><br>${fraudData.level} (${(fraudData.probability * 100).toFixed(0)}%)`;
            document.getElementById('explanation').innerHTML = `<strong>📊 Пояснение:</strong><br>${fraudData.explanation}`;
            
            if (fraudData.red_flags && fraudData.red_flags.length > 0) {
                document.getElementById('explanation').innerHTML += `<br><br><strong>🚩 Красные флаги:</strong><br>${fraudData.red_flags.map(f => `• ${f}`).join('<br>')}`;
            }
        } else {
            document.getElementById('transcript').innerText = `❌ ${data.error || 'Ошибка анализа'}`;
        }
    } catch (err) {
        alert('Ошибка при анализе аудио');
        console.error(err);
        document.getElementById('transcript').innerText = '❌ Ошибка соединения с сервером';
    } finally {
        analyzeBtn.textContent = originalText;
        analyzeBtn.disabled = false;
    }
});

// Сообщить о мошеннике
document.getElementById('reportBtn').addEventListener('click', async () => {
    const phone = document.getElementById('reportPhone').value;
    const city = document.getElementById('reportCity').value;
    const text = document.getElementById('reportText').value;
    const resultDiv = document.getElementById('reportResult');

    if (!phone || !city || !text) {
        resultDiv.innerHTML = '<span style="color: red;">❌ Заполните все поля</span>';
        return;
    }

    resultDiv.innerHTML = '🔄 Отправка...';
    
    try {
        const res = await fetch(`${API_BASE}/report_scam`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, city, text })
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            resultDiv.innerHTML = `<span style="color: green;">✅ ${data.message}</span>`;
            document.getElementById('reportPhone').value = '';
            document.getElementById('reportCity').value = '';
            document.getElementById('reportText').value = '';
            loadMapData(); // обновить карту
        } else {
            resultDiv.innerHTML = `<span style="color: red;">❌ ${data.error || 'Ошибка отправки'}</span>`;
        }
    } catch (err) {
        resultDiv.innerHTML = '<span style="color: red;">❌ Ошибка соединения с сервером</span>';
        console.error(err);
    }
});

// Загрузка данных для карты
async function loadMapData() {
    try {
        const res = await fetch(`${API_BASE}/scam_map`);
        const reports = await res.json();
        updateMap(reports);
    } catch (err) {
        console.error('Не удалось загрузить карту:', err);
    }
}

// Инициализация карты (Leaflet)
let map;
function initMap() {
    map = L.map('map').setView([48.0196, 66.9237], 5);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

function updateMap(reports) {
    if (!map) initMap();
    
    // Очистить старые маркеры
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) map.removeLayer(layer);
    });

    // Координаты городов Казахстана
    const cityCoords = {
        'Алматы': [43.2567, 76.9286],
        'Астана': [51.1694, 71.4491],
        'Шымкент': [42.3417, 69.5901],
        'Караганда': [49.8021, 73.1069],
        'Актобе': [50.2833, 57.1667],
        'Тараз': [42.9, 71.3667],
        'Павлодар': [52.3, 76.95],
        'Усть-Каменогорск': [49.95, 82.6167],
        'Семей': [50.4111, 80.2275],
        'Уральск': [51.2167, 51.3667],
        'Кызылорда': [44.85, 65.5167],
        'Атырау': [47.1167, 51.8833],
        'Костанай': [53.2167, 63.6333],
        'Петропавловск': [54.8667, 69.15],
        'Талдыкорган': [45.0167, 78.3833]
    };

    // Группируем жалобы по городам для счётчика
    const cityReports = {};
    reports.forEach(r => {
        if (!cityReports[r.city]) {
            cityReports[r.city] = [];
        }
        cityReports[r.city].push(r);
    });

    // Добавляем маркеры
    Object.keys(cityReports).forEach(city => {
        const coords = cityCoords[city];
        if (coords) {
            const reportsList = cityReports[city];
            const count = reportsList.length;
            
            L.marker(coords).addTo(map)
                .bindPopup(`
                    <b>📍 ${city}</b><br>
                    <b>📞 Жалоб:</b> ${count}<br>
                    <b>📝 Последняя жалоба:</b><br>
                    Номер: ${reportsList[0].phone}<br>
                    ${reportsList[0].text.substring(0, 100)}${reportsList[0].text.length > 100 ? '...' : ''}
                `);
        }
    });
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    checkServerHealth();
    loadMapData();
    
    // Обновляем карту каждые 30 секунд
    setInterval(loadMapData, 30000);
});