import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Alem.plus API настройки
ALEM_AGENT_URL = os.environ.get("ALEM_AGENT_URL", "https://plus.alem.ai/api/agents/your-agent-id")
ALEM_API_KEY = os.environ.get("ALEM_API_KEY", "your-api-key")

class AlemLLMAnalyzer:
    """Анализ текста через AlemLLM для выявления мошенничества"""
    
    def __init__(self):
        self.system_prompt = """
        Ты — эксперт по выявлению телефонного мошенничества в Казахстане.
        Проанализируй текст разговора и определи, есть ли признаки мошенничества.
        
        Верни ответ ТОЛЬКО в формате JSON:
        {
            "is_fraud": true/false,
            "confidence": 0.0-1.0,
            "reason": "краткое объяснение",
            "fraud_type": "тип мошенничества",
            "red_flags": ["фраза1", "фраза2"]
        }
        
        Типы мошенничества:
        - "bank_fraud" - звонок от "сотрудника банка"
        - "lottery_fraud" - выигрыш/лотерея
        - "family_fraud" - "звоню от имени родственника"
        - "investment_fraud" - инвестиции/криптовалюта
        - "tech_support" - техподдержка/вирусы
        - "other"
        """
    
    def analyze(self, text: str) -> dict:
        """Анализ текста через AlemLLM"""
        if not ALEM_API_KEY or ALEM_API_KEY == "your-api-key":
            # Режим эмуляции (если нет ключа)
            return self._local_analysis(text)
        
        try:
            headers = {
                "Authorization": f"Bearer {ALEM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{ALEM_AGENT_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                return result
            else:
                return self._local_analysis(text)
                
        except Exception as e:
            print(f"AlemLLM error: {e}")
            return self._local_analysis(text)
    
    def _local_analysis(self, text: str) -> dict:
        """Локальный анализ (запасной вариант)"""
        text_lower = text.lower()
        
        fraud_keywords = {
            "bank_fraud": ["банк", "карта", "код", "смс", "реквизиты", "безопасный счет"],
            "lottery_fraud": ["выигрыш", "приз", "лотерея", "налог", "комиссия"],
            "investment_fraud": ["инвестиции", "биткоин", "криптовалюта", "доход"]
        }
        
        for fraud_type, keywords in fraud_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return {
                    "is_fraud": True,
                    "confidence": 0.85,
                    "reason": f"Обнаружены ключевые слова: {keywords}",
                    "fraud_type": fraud_type,
                    "red_flags": [kw for kw in keywords if kw in text_lower]
                }
        
        return {
            "is_fraud": False,
            "confidence": 0.2,
            "reason": "Явных признаков мошенничества не обнаружено",
            "fraud_type": "none",
            "red_flags": []
        }

# Создаём глобальный экземпляр
alem_analyzer = AlemLLMAnalyzer()