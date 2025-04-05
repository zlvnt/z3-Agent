import os
import joblib

base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "model_rf.pkl")
vectorizer_path = os.path.join(base_dir, "vectorizer.pkl")

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

label_map = {
    0: "Negatif",
    1: "Netral",
    2: "Positif"
}

def analyze_sentiment(text):
    X = vectorizer.transform([text])
    prediction = model.predict(X)[0]
    return label_map.get(prediction, "Netral")