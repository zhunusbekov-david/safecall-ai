import numpy as np
import librosa
import os

def detect_ai_voice(audio_path):
    try:
        if not os.path.exists(audio_path):
            return {
                "error": "Файл не найден"
            }

        y, sr = librosa.load(audio_path, sr=16000, duration=30)

        if len(y) == 0:
            return {
                "error": "Пустой аудиофайл"
            }

        # Нормализация
        y = librosa.util.normalize(y)

        # --- 1. Pitch (основной тон)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[pitches > 0]
        pitch_std = np.std(pitch_values) if len(pitch_values) > 0 else 0

        # --- 2. Энергия
        rms = librosa.feature.rms(y=y)[0]
        energy_std = np.std(rms)

        # --- 3. Zero Crossing Rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_std = np.std(zcr)

        # --- 4. Спектральная центроид
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_std = np.std(spectral_centroid)

        # --- 5. MFCC (ключевой параметр)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_std = np.mean(np.std(mfcc, axis=1))

        # --- 6. Спектральная ширина
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        bandwidth_std = np.std(spectral_bandwidth)

        # --- 7. Темп (дополнительный)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if isinstance(tempo, np.ndarray):
            tempo = tempo[0] if len(tempo) > 0 else 120

        # -------------------------
        # Нормализация признаков
        # -------------------------
        features = {
            "pitch_std": pitch_std,
            "energy_std": energy_std,
            "zcr_std": zcr_std,
            "centroid_std": centroid_std,
            "mfcc_std": mfcc_std,
            "bandwidth_std": bandwidth_std,
            "tempo": tempo
        }

        # -------------------------
        # Взвешенная система (почти ML)
        # -------------------------
        score = 0

        # Pitch (монотонность)
        if pitch_std < 15:
            score += 2
        elif pitch_std < 25:
            score += 1

        # Энергия
        if energy_std < 0.015:
            score += 2
        elif energy_std < 0.03:
            score += 1

        # ZCR
        if zcr_std < 0.008:
            score += 1

        # Центроид
        if centroid_std < 400:
            score += 2
        elif centroid_std < 800:
            score += 1

        # MFCC (самый важный)
        if mfcc_std < 15:
            score += 3
        elif mfcc_std < 25:
            score += 2

        # Спектральная ширина
        if bandwidth_std < 500:
            score += 1

        # Темп (слабый фактор)
        if tempo < 90:
            score += 1

        # -------------------------
        # Probability (как AI модель)
        # -------------------------
        max_score = 12
        probability = min(score / max_score, 1.0)

        confidence_percent = int(probability * 100)

        # -------------------------
        # Финальное решение
        # -------------------------
        if probability >= 0.7:
            label = "AI voice"
        elif probability >= 0.4:
            label = "Uncertain"
        else:
            label = "Human voice"

        return {
            "label": label,
            "confidence": f"{confidence_percent}%",
            "raw_score": score,
            "features": features
        }

    except Exception as e:
        return {
            "error": str(e)[:100]
        }