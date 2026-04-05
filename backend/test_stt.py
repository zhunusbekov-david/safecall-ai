from speech_to_text import stt_recognizer

# Укажи путь к любому аудиофайлу (wav или webm)
result = stt_recognizer.transcribe("C:\Users\david\Downloads\WhatsApp Ptt 2026-04-03 at 17.25.02.wav.ogg", language="ru")
print(result)