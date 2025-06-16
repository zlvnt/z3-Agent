import os
from dotenv import load_dotenv
from google import genai

# Load .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ API key tidak ditemukan. Cek .env.")
    exit(1)

# Inisialisasi client
client = genai.Client(api_key=GEMINI_API_KEY)

print("🧠 Gemini Chat (via client = genai.Client) — CTRL+C untuk keluar\n")

while True:
    try:
        user_input = input("👤 Kamu: ")
        if not user_input.strip():
            continue

        response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": user_input}]}]
        )

        print(f"🤖 Gemini: {response.text.strip()}\n")

    except KeyboardInterrupt:
        print("\n🚪 Keluar...")
        break
    except Exception as e:
        print(f"❌ Error: {e}\n")
