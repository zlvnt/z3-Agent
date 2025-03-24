import pandas as pd

file_path = "comments_for_labeling.csv" 
df = pd.read_csv(file_path)

def label_sentiment(comment):
    comment = str(comment).lower()
    if any(word in comment for word in ["keren", "bagus", "mantap", "hebat", "terbaik", "semoga sehat", "makasih"]):
        return "Positif"
    elif any(word in comment for word in ["sotoy", "jelek", "buruk", "gagal", "parah", "stress", "sok asik", "cokk"]):
        return "Negatif"
    else:
        return "Netral"

df["sentiment_label"] = df["comment"].apply(label_sentiment)

output_file = "labeled_comments.csv" 
df.to_csv(output_file, index=False, encoding="utf-8")

print(f"✅ Labeling selesai! File tersimpan sebagai '{output_file}'.")
