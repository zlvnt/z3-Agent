import os
import requests
import json
import random
import time
from dotenv import load_dotenv
from rf_model import analyze_sentiment

# API
load_dotenv()
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# AI API
from google import genai
client = genai.Client(api_key=GEMINI_API_KEY)

base_dir = os.path.dirname(os.path.abspath(__file__))
PERSONALITY_FILE = os.path.join(base_dir, "personality1.json")

# LOAD PERSONALITY
def load_personality():
    try:
        with open(PERSONALITY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("❌ File personality.json tidak ditemukan.")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
    return {}

def get_post_data(post_id):
    personality_data = load_personality()
    posts = personality_data.get("posts", [])
    for post in posts:
        if post.get("post_id") == post_id:
            return post
    return None

def get_previous_caption(current_post_id):
    posts = load_personality().get("posts", [])
    for i, post in enumerate(posts):
        if post["post_id"] == current_post_id and i > 0:
            return posts[i - 1]["caption"]
    return ""

# CAPTION
def generate_caption(image_description="", content_type="lifestyle", previous_caption=""):
    personality_data = load_personality()

    if not personality_data:
        print("❌ Error: JSON personality tidak bisa dimuat.")
        return "Caption tidak dapat dibuat."

    prompt_template = personality_data.get("prompts", {}).get("caption", "")

    if not prompt_template:
        print("❌ Error: Prompt caption tidak ditemukan dalam JSON.")
        return "Caption tidak dapat dibuat."

    # TONE (IF NOT = LIFESTYLE)
    tone = personality_data.get("tone", {}).get(content_type, personality_data.get("tone", {}).get("lifestyle", ""))

    # Format prompt
    prompt = prompt_template.format(
        identity_name=personality_data.get("identity", {}).get("name", ""),
        identity_role=personality_data.get("identity", {}).get("role", ""),
        identity_goal=personality_data.get("identity", {}).get("goal", ""),
        identity_style=personality_data.get("identity", {}).get("style", ""),
        image_description=image_description or "Tidak ada deskripsi gambar. Buat caption bebas berdasarkan tren sosial media dan niche yang sesuai.",
        tone=tone,
        caption_do_rules="\n  - " + "\n  - ".join(personality_data.get("rules", {}).get("caption_do", [])),
        dont_rules="\n  - " + "\n  - ".join(personality_data.get("rules", {}).get("dont", [])),
        previous_caption=previous_caption
    )

    try:
        response = client.models.generate_content(
            model="models/gemini-1.5-pro",
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        caption = response.text.strip() if response and response.text else "AI tidak dapat menghasilkan caption."

        # Debugging Output
        print(f"📝 Caption Generated: {caption}")

        return caption
    except Exception as e:
        print("❌ Error AI:", str(e))
        return "Caption tidak dapat dibuat."

def upload_photo(image_url, image_description, content_type="edukasi"):
    """Mengunggah foto ke Instagram dan menyimpan post ID jika berhasil."""
    print("📤 Mengunggah foto ke Instagram...")

    # Buat caption menggunakan AI
    caption = generate_caption(image_description, content_type)

    url = f"https://graph.facebook.com/v18.0/{ACCOUNT_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }

    try:
        response = requests.post(url, data=payload).json()
        if "id" not in response:
            print(f"❌ Gagal mengunggah foto: {response}")
            return None
    except Exception as e:
        print(f"❌ Error saat mengunggah foto: {str(e)}")
        return None

    creation_id = response["id"]
    print(f"✅ Foto berhasil diunggah dengan ID: {creation_id}")

    # publikasi foto
    publish_url = f"https://graph.facebook.com/v18.0/{ACCOUNT_ID}/media_publish"
    try:
        publish_response = requests.post(publish_url, data={
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN
        }).json()

        if "id" in publish_response:
            post_id = publish_response["id"]
            print(f"✅ Foto berhasil dipublikasikan! Post ID: {post_id}")

            # SIMPAN DATA
            save_post_data(post_id, caption)

            return post_id
        else:
            print(f"❌ Gagal mempublikasikan foto: {publish_response}")
            return None
    except Exception as e:
        print(f"❌ Error saat mempublikasikan foto: {str(e)}")
        return None    

# SIMPAN DATA
def save_post_data(post_id, caption):
    personality_data = load_personality()

    if "posts" not in personality_data:
        personality_data["posts"] = []

    # STRUKTUR
    new_post = {
        "post_id": post_id,
        "caption": caption
    }

    personality_data["posts"].append(new_post)

    # Simpan ke JSON
    with open(PERSONALITY_FILE, "w", encoding="utf-8") as file:
        json.dump(personality_data, file, indent=2)

    print(f"📝 Postingan disimpan: {post_id} - {caption}")

CONVERSATION_FILE = os.path.join(base_dir, "conversations.json")

# LOAD PERCAKAPAN
def load_conversations():
    if not os.path.exists(CONVERSATION_FILE):
        return {"conversations": {}}

    with open(CONVERSATION_FILE, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {"conversations": {}}

#SIMPAN PERCAKAPAN
def save_conversation(post_id, comment_id, user, comment, reply, sentiment):
    conversations = load_conversations()

    # Buat struktur JSON jika belum ada
    if post_id not in conversations["conversations"]:
        conversations["conversations"][post_id] = {}

    if comment_id not in conversations["conversations"][post_id]:
        conversations["conversations"][post_id][comment_id] = []

    # Cek apakah balasan sudah ada untuk menghindari duplikasi
    existing_replies = [entry["reply"] for entry in conversations["conversations"][post_id][comment_id]]
    if reply in existing_replies:
        print("⚠️ Balasan sudah ada, tidak perlu disimpan ulang.")
        return

    # Tambahkan ke dalam JSON
    conversations["conversations"][post_id][comment_id].append({
        "user": user,
        "comment": comment,
        "reply": reply,
        "sentiment": sentiment
    })

    try:
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as file:
            json.dump(conversations, file, indent=2)
            file.flush()
    except Exception as e:
        print(f"❌ Gagal menyimpan percakapan: {str(e)}")

# GENERATE KOMENTER
def generate_reply(comment, post_id, comment_id, username):

    # Load personality
    personality_data = load_personality()
    sentiment = analyze_sentiment(comment)

    # Debug
    post_data = get_post_data(post_id)
    if not post_data:
        print("⚠️ Post data tidak ditemukan, AI menggunakan balasan default.")
        return "Eror gua coo"

    post_caption = post_data.get("caption", "Tanpa konteks.")
    tone = post_data.get("tone", "")

    # Ambil riwayat percakapan sebelumnya
    conversations = load_conversations()
    conversation_history = conversations.get("conversations", {}).get(post_id, {}).get(comment_id, [])

    # Limit Menyimpan Komentar
    history_limit = 5
    context = ""
    if conversation_history:
        limited_history = conversation_history[-history_limit:]
        context = "Riwayat Percakapan:\n"
        for chat in limited_history:
            context += f"{chat['user']}: {chat['comment']}\n"
            context += f"z3: {chat['reply']}\n"

    identity = personality_data.get("identity", {})
    identxt = json.dumps(identity, indent=2, ensure_ascii=False)

    reply_do_rules = "\n  - " + "\n  - ".join(personality_data.get("rules", {}).get("reply_do", []))
    dont_rules = "\n  - " + "\n  - ".join(personality_data.get("rules", {}).get("dont", []))

    # Prompt dari JSON
    reply_prompt_template = personality_data.get("prompts", {}).get("reply", "")
    if not reply_prompt_template:
        print("⚠️ Template prompt tidak ditemukan di JSON.")
        return "AI tidak bisa merespons saat ini."

    # Buat prompt berdasarkan template dari JSON
    prompt = reply_prompt_template.format(
        identity=identxt,
        post_caption=post_caption,
        context=context,
        username=username,
        comment=comment,
        tone=tone,
        sentiment=sentiment,
        reply_do_rules=reply_do_rules,
        dont_rules=dont_rules
    )

    # JIKA AI GAGAL BALES
    try:
        response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        ai_reply = response.text.strip() if response and response.text and response.text.strip() else "AI gagal merespons."
    except Exception as e:
        print(f"❌ Error saat generate reply: {str(e)}")
        ai_reply = "Eror gua coo"

    # Debugging
    print(f"🤖 AI Reply Generated: {ai_reply}")

    # Simpan percakapan
    save_conversation(post_id, comment_id, username, comment, ai_reply, sentiment)

    return ai_reply

# use
if __name__ == "__main__":
    image_url = "https://i.imgur.com/PXETVN6.jpeg"
    image_description = "udah lama gak update euyy"  
    content_type = "edukasi"  

    # Unggah foto ke Instagram
    post_id = upload_photo(image_url, image_description, content_type)
