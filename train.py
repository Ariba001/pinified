import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

data = {
    "aadhaar": [1, 1, 0, 1],
    "bank": [1, 0, 0, 1],
    "rc": [1, 0, 1, 1],
    "score": [100, 60, 40, 90]
}

df = pd.DataFrame(data)

X = df[["aadhaar", "bank", "rc"]]
y = df["score"]

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, "model.pkl")