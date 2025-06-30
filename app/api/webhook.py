from flask import Flask, request, jsonify
import json

from Instagram_AI_Agent.app.config import ACCESS_TOKEN, VERIFY_TOKEN
from Instagram_AI_Agent.app.agent.langchain_z3 import generate_reply
from Instagram_AI_Agent.app.services.instagram_api import upload_reply

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Unauthorized", 403

    payload = request.json or {}
    print("\n📩  Incoming Webhook Data:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    entries = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue

            comment_data = change["value"]
            comment_id   = comment_data.get("parent_id") or comment_data.get("id")
            post_id      = comment_data.get("media", {}).get("id", "unknown_post")
            comment_text = comment_data.get("text", "")
            username     = comment_data.get("from", {}).get("username", "")

            if username.lower() == "z3_agent":
                print(f"⚠️  Detected self‑comment — skipping (id={comment_id})")
                continue

            ai_reply = generate_reply(
                comment_text,
                post_id=post_id,
                comment_id=comment_id,
                username=username,
            )
            print("🤖  AI reply:", ai_reply)

            api_resp = upload_reply(comment_id, ai_reply)
            print("🚀  IG API response:", api_resp)

    return jsonify(status="ok"), 200


if __name__ == "__main__":
    app.run(port=5001, debug=True)
