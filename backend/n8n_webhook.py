import os
import requests
from datetime import datetime

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "")

class N8NAutomation:
    """
    Автоматизация через n8n:
    - При новой жалобе → уведомление всем пользователям
    - При высоком риске → срочное оповещение
    - Статистика мошенников в реальном времени
    """
    
    @staticmethod
    def trigger_on_new_fraud(phone: str, city: str, description: str):
        """Отправка события в n8n при новой жалобе"""
        if not N8N_WEBHOOK_URL:
            print("n8n webhook not configured")
            return
        
        try:
            payload = {
                "event": "new_fraud_report",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "phone": phone,
                    "city": city,
                    "description": description,
                    "risk_level": "high"
                }
            }
            
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"n8n error: {e}")
            return False
    
    @staticmethod
    def trigger_fraud_alert(phone: str, risk_score: float):
        """Срочное оповещение о мошеннике"""
        if not N8N_WEBHOOK_URL:
            return
        
        try:
            payload = {
                "event": "fraud_alert",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "phone": phone,
                    "risk_score": risk_score,
                    "action_required": True
                }
            }
            
            requests.post(f"{N8N_WEBHOOK_URL}/alert", json=payload, timeout=3)
            
        except Exception as e:
            print(f"Alert error: {e}")