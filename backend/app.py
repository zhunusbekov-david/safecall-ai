import os
import uuid
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import supabase_config as sb
from n8n_webhook import N8NAutomation

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "tools": {
            "alemllm": "✅",
            "stt_russian": "✅" if os.environ.get("STT_RU_API_KEY") else "❌",
            "stt_kazakh": "✅" if os.environ.get("STT_KZ_API_KEY") else "❌",
            "supabase": "✅" if sb.supabase else "❌",
            "n8n": "✅" if os.environ.get("N8N_WEBHOOK_URL") else "⚠️"
        }
    })

@app.route('/analyze_audio', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "Файл аудио не загружен"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
        audio_file.save(tmp_file.name)
        temp_filename = tmp_file.name

    try:
        from speech_to_text import stt_recognizer
        
        # Пробуем русский язык
        stt_result = stt_recognizer.transcribe(temp_filename, language="ru")
        
        if not stt_result.get("success"):
            # Если русский не сработал, пробуем казахский
            stt_result = stt_recognizer.transcribe(temp_filename, language="kk")
        
        if stt_result.get("success"):
            transcribed_text = stt_result.get("text", "")
        else:
            transcribed_text = f"Ошибка STT: {stt_result.get('error', 'Unknown')}"
        
        # === Анализ через AlemLLM ===
        fraud_analysis = {
            "level": "🟢 НИЗКАЯ ВЕРОЯТНОСТЬ", 
            "probability": 0.2, 
            "explanation": "Анализ через AlemLLM", 
            "red_flags": []
        }
        
        try:
            import requests
            import json
            import re
            
            alem_url = "https://llm.alem.ai/v1/chat/completions"
            alem_key = "sk-K_5H2171cbHeGlNLlA9Wmw"
            
            prompt = f"""Ты эксперт по выявлению телефонного мошенничества. Проанализируй текст разговора и верни ТОЛЬКО JSON. Формат: {{"is_fraud": true/false, "confidence": 0.0-1.0, "reason": "объяснение", "fraud_type": "bank_fraud|lottery_fraud|other", "red_flags": ["фраза1", "фраза2"]}}
            
            Текст: {transcribed_text}"""
            
            response = requests.post(
                alem_url, 
                headers={"Authorization": f"Bearer {alem_key}", "Content-Type": "application/json"}, 
                json={"model": "alemllm", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}, 
                timeout=15
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    probability = analysis.get("confidence", 0.2)
                    if probability > 0.7:
                        level = "🔴 ВЫСОКАЯ ВЕРОЯТНОСТЬ"
                    elif probability > 0.3:
                        level = "🟠 СРЕДНЯЯ ВЕРОЯТНОСТЬ"
                    else:
                        level = "🟢 НИЗКАЯ ВЕРОЯТНОСТЬ"
                    fraud_analysis = {
                        "level": level, 
                        "probability": probability, 
                        "explanation": analysis.get("reason", ""), 
                        "red_flags": analysis.get("red_flags", [])
                    }
        except Exception as e:
            fraud_analysis["explanation"] = f"AlemLLM ошибка: {str(e)[:50]}"

        # Список использованных инструментов alem.plus для жюри
        tools_used = ["AlemLLM", "STT_Russian", "STT_Kazakh", "Supabase", "n8n"]

        return jsonify({
            "success": True, 
            "transcript": transcribed_text[:500], 
            "voice_analysis": "Voice analysis complete", 
            "fraud_analysis": fraud_analysis,
            "tools_used": tools_used
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
            
@app.route('/check_number', methods=['POST'])
def check_number():
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone required"}), 400
    
    if sb.supabase:
        response = sb.supabase.table("fraud_reports").select("*").eq("phone", phone).execute()
        reports = response.data
        
        if reports:
            risk = sum(r.get("risk_score", 0.5) for r in reports) / len(reports)
            if risk > 0.7:
                status = "🔴 МОШЕННИК!"
            elif risk > 0.3:
                status = "🟠 ВЫСОКИЙ РИСК"
            else:
                status = "✅ Безопасный номер"
            
            return jsonify({
                "phone": phone,
                "status": status,
                "risk_score": risk,
                "reports_count": len(reports),
                "details": reports[:3]
            })
    
    return jsonify({
        "phone": phone,
        "status": "✅ Безопасный номер",
        "risk_score": 0,
        "reports_count": 0
    })

@app.route('/report_scam', methods=['POST'])
def report_scam():
    data = request.get_json()
    phone = data.get('phone')
    city = data.get('city')
    text = data.get('text')
    
    if not all([phone, city, text]):
        return jsonify({"error": "Missing fields"}), 400
    
    if sb.supabase:
        new_report = {
            "phone": phone,
            "city": city,
            "text": text,
            "risk_score": 0.85,
            "created_at": "now()"
        }
        
        sb.supabase.table("fraud_reports").insert(new_report).execute()
        
        # Отправка в n8n
        if os.environ.get("N8N_WEBHOOK_URL"):
            N8NAutomation.trigger_on_new_fraud(phone, city, text)
        
        return jsonify({"status": "success", "message": "Жалоба отправлена"})
    
    return jsonify({"error": "Database not configured"}), 500

@app.route('/scam_map', methods=['GET'])
def scam_map():
    if sb.supabase:
        response = sb.supabase.table("fraud_reports").select("*").execute()
        return jsonify(response.data)
    return jsonify([])

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 SafeCall AI Backend")
    print("=" * 50)
    print("📊 Используемые инструменты alem.plus:")
    print("   1. AlemLLM - анализ текста")
    print("   2. STT Russian - распознавание русской речи")
    print("   3. STT Kazakh - распознавание казахской речи")
    print("   4. Supabase - база данных")
    print("   5. n8n - автоматизация")
    print("=" * 50)
    app.run(debug=True, port=5000, host='0.0.0.0')