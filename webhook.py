from flask import Flask, request
import requests
import json
from config import ACCESS_TOKEN, VERIFY_TOKEN
from langchain_z3 import generate_reply
from conversation import save_conversation

app = Flask(__name__)

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
        print(f"📩 Webhook Data: {json.dumps(data, indent=2)}")
        return "OK", 200

if __name__ == '__main__':
    app.run(port=5001, debug=True)