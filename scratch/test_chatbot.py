import requests
import sys

# Reconfigure stdout to use UTF-8 encoding to avoid Windows UnicodeEncodeErrors
sys.stdout.reconfigure(encoding='utf-8')

session = requests.Session()

# 1. Test GET /chatbot
print("--- 1. Testing GET /chatbot ---")
url = "http://localhost:5000/chatbot"
r = session.get(url)
print("Status code:", r.status_code)
print("Contains '<script' (lowercased):", "<script" in r.text.lower())
print("Contains 'Assistant Météo IA':", "Assistant Météo IA" in r.text)
print("Contains navigation link to /chatbot:", 'href="/chatbot"' in r.text)
print("Contains welcome message:", "Bonjour" in r.text)

# 2. Test POST /chatbot sending a message
print("\n--- 2. Testing POST /chatbot with user message ---")
payload = {
    "user_input": "Quelles sont les précautions pour la qualité de l'air ?"
}
r2 = session.post(url, data=payload, allow_redirects=True)
print("POST status code:", r2.status_code)
print("Final URL after redirect:", r2.url)
print("Contains '<script' (lowercased):", "<script" in r2.text.lower())
print("Contains user message in history:", "Quelles sont les précautions" in r2.text)
print("Contains assistant response prefix:", "avatar-icon" in r2.text)

# Check if AI replied in French and check formatting
print("AI Response HTML Snippet:")
# Find last message bubble containing AI response
import re
bubbles = re.findall(r'<div class="message-bubble">.*?</div>', r2.text, re.DOTALL)
if bubbles:
    for idx, bubble in enumerate(bubbles):
        print(f"Bubble {idx}: {bubble.strip()[:400]}...")
else:
    print("No message bubbles found in response HTML.")

# 3. Test Reset
print("\n--- 3. Testing POST /chatbot reset ---")
payload_reset = {
    "action": "reset"
}
r3 = session.post(url, data=payload_reset, allow_redirects=True)
print("Reset status code:", r3.status_code)
print("Contains reset confirmation message:", "réinitialisée" in r3.text or "reinitialisee" in r3.text)
print("Contains previous user message (should be False):", "Quelles sont les précautions" in r3.text)
