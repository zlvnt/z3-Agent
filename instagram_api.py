import requests
from config import ACCESS_TOKEN

def upload_reply(comment_id, message):
    """
    Membalas komentar di Instagram.
    - comment_id: ID komentar yang ingin dibalas (atau parent)
    - message: Teks balasan
    """
    url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
    payload = {
        "message": message,
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    result = response.json()
    if "error" in result:
        print(f"❌ Gagal membalas komentar: {result['error']['message']}")
    else:
        print(f"✅ Berhasil membalas: {message}")
    return result