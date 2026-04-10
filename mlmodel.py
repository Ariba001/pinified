import joblib

model = joblib.load("model.pkl")


def predict_score(lead):
    features = [[
        1 if lead.aadhaar_status == "submitted" else 0,
        1 if lead.bank_status == "submitted" else 0,
        1 if lead.rc_status == "submitted" else 0
    ]]

    return int(model.predict(features)[0])