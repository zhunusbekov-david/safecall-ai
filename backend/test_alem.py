import requests

url = "https://llm.alem.ai/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-K_5H2171cbHeGlNLlA9Wmw",
    "Content-Type": "application/json"
}
data = {
    "model": "alemllm",
    "messages": [{"role": "user", "content": "Привет! Ты работаешь?"}]
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.json())