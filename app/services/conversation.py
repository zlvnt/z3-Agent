import json
import os
from Instagram_AI_Agent.app.config import CONVERSATIONS_PATH

def load_conversations(path=CONVERSATIONS_PATH):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = json.load(f)
    if "conversations" in data:
        return data["conversations"]
    else:
        return data

def save_conversations(conversations, path=CONVERSATIONS_PATH):
    with open(path, "w") as f:
        json.dump({"conversations": conversations}, f, indent=2)

def get_conversation(post_id, path=CONVERSATIONS_PATH):
    conversations = load_conversations(path)
    return conversations.get(post_id, {})

def append_comment(post_id, comment_id, user, comment, reply, path=CONVERSATIONS_PATH):
    conversations = load_conversations(path)
    if post_id not in conversations:
        conversations[post_id] = {}
    if comment_id not in conversations[post_id]:
        conversations[post_id][comment_id] = []
    conversations[post_id][comment_id].append({
        "user": user,
        "comment": comment,
        "reply": reply
    })
    save_conversations(conversations, path)

def get_comment_history(post_id, comment_id, path=CONVERSATIONS_PATH):
    conversations = load_conversations(path)
    return conversations.get(post_id, {}).get(comment_id, [])
