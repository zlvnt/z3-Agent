import json
import pandas as pd

with open("conversations.json", "r", encoding="utf-8") as file:
    data = json.load(file)

comments_data = []

for post_id, comments in data["conversations"].items():
    for comment_thread in comments.values():
        for entry in comment_thread:
            user = entry["user"]
            comment = entry["comment"]
            comments_data.append([user, comment, ""]) 

df = pd.DataFrame(comments_data, columns=["user", "comment", "sentiment_label"])

df.to_csv("comments_for_labeling.csv", index=False, encoding="utf-8")

print("✅ Data komentar berhasil diekstrak! Silakan labeli secara manual di 'comments_for_labeling.csv'")
