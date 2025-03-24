from flask import Flask, request
import requests
import json
import os
from dotenv import load_dotenv
from agent_gemini import generate_reply

app = Flask(__name__)

# API
load_dotenv()
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
VERIFY_TOKEN = "1234z"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Unauthorized", 403
    
    elif request.method == 'POST':
        data = request.json
        print(f"📩 Webhook Data: {json.dumps(data, indent=2)}")  # Debugging
        
        if data and "entry" in data:
            for entry in data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change["field"] == "comments":
                            comment_data = change["value"]
                            comment_id = comment_data.get("parent_id", comment_data["id"])
                            comment_text = comment_data["text"]
                            post_id = comment_data.get("media", {}).get("id", "unknown_post")
                            commenter_username = comment_data["from"]["username"]

                            # CEGAH LOOP
                            if commenter_username == "z3_agent":
                                print(f"⚠️ AI mendeteksi komentarnya sendiri ({comment_text}), skip balasan...")
                                continue

                            # Proses AI Auto-Replys
                            reply_text = generate_reply(comment_text, post_id, comment_id, commenter_username)

                            # Kirim ke Instagram
                            url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
                            payload = {"message": reply_text, "access_token": ACCESS_TOKEN}
                            response = requests.post(url, data=payload).json()

                            if "error" in response:
                                print(f"❌ Gagal membalas komentar: {response['error']['message']}")
                            else:
                                print(f"✅ Berhasil membalas: {reply_text}")

        return "OK", 200

if __name__ == '__main__':
    app.run(port=5001, debug=True)
