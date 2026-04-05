import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Проверяем, есть ли реальный API ключ
ALEM_AGENT_URL = os.environ.get("ALEM_AGENT_URL")
ALEM_API_KEY = os.environ.get("ALEM_API_KEY")

# Простая локальная модель анализа мошенничества
class LocalFraudDetector:
    def __init__(self):
        # Словарь ключевых слов мошенничества (русский и казахский)
        self.fraud_keywords = {
            # Русские ключевые слова
            'ru': [
                'код подтверждения', 'карта', 'реквизиты', 'перевод', 'деньги',
                'выигрыш', 'приз', 'лотерея', 'налог', 'комиссия', 'безопасный счет',
                'личный кабинет', 'пароль', 'смс', 'банк', 'сотрудник банка',
                'служба безопасности', 'подозрительная операция', 'заблокирован',
                'инвестиции', 'биткоин', 'криптовалюта', 'оформить кредит',
                'верните деньги', 'переведите средства', 'личные данные'
            ],
            # Казахские ключевые слова
            'kk': [
                'кодты растау', 'карта', 'деректемелер', 'аударым', 'ақша',
                'ұтыс', 'сыйлық', 'лотерея', 'салық', 'комиссия', 'қауіпсіз шот',
                'жеке кабинет', 'құпия сөз', 'смс', 'банк', 'банк қызметкері',
                'қауіпсіздік қызметі', 'күдікті операция', 'бұғатталды',
                'инвестиция', 'биткоин', 'криптовалюта', 'несие ресімдеу',
                'ақшаны қайтарыңыз', 'ақша аударыңыз', 'жеке деректер'
            ]
        }
        
        # Паттерны мошеннических фраз
        self.fraud_patterns = [
            r'(переведи|переведите).*(деньги|средства)',
            r'(сообщи|скажи).*(код|пароль)',
            r'(оформить|взять).*(кредит|займ)',
            r'(выиграл|победил).*(приз|лотерея)',
            r'(безопасный счет|безопасный счёт)',
            r'(служба безопасности банка)',
            r'(подозрительная операция)',
        ]
        
        # Положительные ключевые слова (уменьшают риск)
        self.safe_keywords = [
            'извините', 'ошибся', 'не туда попал', 'до свидания',
            'не интересно', 'положите трубку', 'мошенники'
        ]
    
    def analyze(self, text):
        """Анализирует текст и возвращает результат"""
        if not text or len(text.strip()) < 10:
            return {
                "fraud_probability": 0.3,
                "explanation": "Недостаточно текста для анализа",
                "red_flags": ["Короткое сообщение"]
            }
        
        text_lower = text.lower()
        score = 0.5  # начальная нейтральная оценка
        red_flags = []
        
        # Проверка ключевых слов мошенничества (русские)
        for keyword in self.fraud_keywords['ru']:
            if keyword in text_lower:
                score += 0.15
                red_flags.append(f"Обнаружено ключевое слово: '{keyword}'")
                if len(red_flags) >= 5:
                    break
        
        # Проверка ключевых слов мошенничества (казахские)
        for keyword in self.fraud_keywords['kk']:
            if keyword in text_lower:
                score += 0.15
                red_flags.append(f"Анықталған кілт сөз: '{keyword}'")
                if len(red_flags) >= 5:
                    break
        
        # Проверка паттернов
        for pattern in self.fraud_patterns:
            if re.search(pattern, text_lower):
                score += 0.2
                red_flags.append(f"Обнаружен подозрительный паттерн: '{pattern}'")
                break
        
        # Проверка безопасных слов (снижают риск)
        for keyword in self.safe_keywords:
            if keyword in text_lower:
                score -= 0.15
                break
        
        # Ограничиваем score от 0 до 1
        score = max(0.0, min(1.0, score))
        
        # Генерация объяснения
        if score >= 0.7:
            explanation = "Высокая вероятность мошенничества. Обнаружены типичные признаки телефонного мошенничества: запрос личных данных, финансовых реквизитов или кодов подтверждения."
        elif score >= 0.4:
            explanation = "Средняя вероятность мошенничества. Рекомендуется быть осторожным и не сообщать личные данные."
        else:
            explanation = "Низкая вероятность мошенничества. Разговор не содержит типичных признаков мошенничества."
        
        # Убираем дубликаты в red_flags
        red_flags = list(dict.fromkeys(red_flags))[:5]
        
        return {
            "fraud_probability": score,
            "explanation": explanation,
            "red_flags": red_flags if red_flags else ["Явных признаков мошенничества не обнаружено"]
        }

# Создаём экземпляр детектора
local_detector = LocalFraudDetector()

def analyze_text_for_fraud(text: str):
    """
    Анализ текста на предмет мошенничества.
    Использует локальный детектор, пока нет API ключа AlemLLM.
    """
    # Проверяем, настроен ли AlemLLM
    if ALEM_AGENT_URL and ALEM_API_KEY and ALEM_API_KEY != "ваш_api_ключ_агента":
        try:
            # Пытаемся использовать реальный AlemLLM
            import requests
            
            headers = {
                "Authorization": f"Bearer {ALEM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "user", 
                        "content": f"Проанализируй этот текст разговора на предмет мошенничества. Верни JSON с полями: fraud_probability (0-1), explanation, red_flags (массив). Текст: {text}"
                    }
                ]
            }
            
            response = requests.post(ALEM_AGENT_URL, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                try:
                    result = json.loads(content)
                    return result
                except:
                    pass  # если не JSON, используем локальный анализ
        except:
            pass  # при любой ошибке используем локальный анализ
    
    # Используем локальный анализ
    return local_detector.analyze(text)

# Для тестирования локально
if __name__ == "__main__":
    # Тестовые примеры
    test_texts = [
        "Здравствуйте, я сотрудник банка. Ваша карта заблокирована. Назовите код из смс для разблокировки.",
        "Привет, как дела? Просто звоню узнать, как ты.",
        "Вы выиграли автомобиль! Для получения приза нужно оплатить налог 50 000 тенге.",
        "Сәлем, мен банк қызметкерімін. Сіздің картаңыз бұғатталды. СМС-тегі кодты айтыңыз."
    ]
    
    print("Тестирование локального детектора мошенничества:\n")
    for text in test_texts:
        result = analyze_text_for_fraud(text)
        print(f"Текст: {text[:50]}...")
        print(f"Вероятность мошенничества: {result['fraud_probability']*100:.0f}%")
        print(f"Объяснение: {result['explanation']}")
        print(f"Красные флаги: {', '.join(result['red_flags'])}")
        print("-" * 50) 