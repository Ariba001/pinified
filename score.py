def calculate_score(lead):
    score = 0

    if lead.aadhaar_status == "submitted":
        score += 30
    if lead.bank_status == "submitted":
        score += 30
    if lead.rc_status == "submitted":
        score += 40

    return score