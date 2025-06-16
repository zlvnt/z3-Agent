import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("❌ API key Gemini belum tersedia. Set dulu di .env atau environment variable.")
    exit(1)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
)

print("🧠 Gemini Chat (CTRL+C to exit)")
while True:
    try:
        user_input = input("👤 Kamu: ")
        response = llm.invoke(user_input)
        print(f"🤖 Gemini: {response}")
    except KeyboardInterrupt:
        print("\n🚪 Keluar...")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
