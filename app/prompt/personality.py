import json
from Instagram_AI_Agent.app.config import PERSONALITY_PATH

def load_personality(path=PERSONALITY_PATH):
    with open(path, "r") as f:
        data = json.load(f)
    return data

def get_prompt(personality, prompt_type="caption"):
    return personality.get("prompts", {}).get(prompt_type, "")

def get_post_by_id(personality, post_id):
    for post in personality.get("posts", []):
        if post.get("post_id") == post_id:
            return post
    return None

def get_caption_by_post_id(personality, post_id):
    post = get_post_by_id(personality, post_id)
    if post:
        return post.get("caption", "")
    return ""

