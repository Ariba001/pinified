from database import SessionLocal
import pandas as pd
from datetime import datetime
from models import Lead, Communication
import json
from llm import call_llm

def ingestion_agent(file_path):
    db = SessionLocal()

    df = pd.read_csv(file_path)

    inserted = 0
    errors = []

    for index, row in df.iterrows():
        try:
            if not row.get("name") or not row.get("phone"):
                errors.append(f"Row {index}: Missing name or phone")
                continue

            lead_data = {
                "name": str(row.get("name")).strip(),
                "phone": str(row.get("phone")).strip(),
                "email": str(row.get("email")).strip(),
                "city": str(row.get("city")).strip(),
                "vehicle_type": str(row.get("vehicle_type")).strip(),
                "vehicle_count": int(row.get("vehicle_count", 0)),
                "aadhaar_status": row.get("aadhaar_status", "pending"),
                "bank_status": row.get("bank_status", "pending"),
                "rc_status": row.get("rc_status", "pending"),
                "app_installed": row.get("app_installed", "no"),
                "preferred_channel": row.get("preferred_channel", "whatsapp"),
            }

            lead = Lead(**lead_data)
            db.add(lead)
            inserted += 1

        except Exception as e:
            errors.append(f"Row {index}: {str(e)}")

    db.commit()

    return {
        "inserted": inserted,
        "errors": errors
    }

def understanding_agent(state):
    message = state["message"]
    context = retrieve_context(state["lead"])
    history = get_history(state["lead"].lead_id)

    prompt = f"""
You are an AI onboarding assistant.

Extract structured data from the user message.

Message: "{message}"
Context: "{context}"
Recent History: "{history}"

Return ONLY valid JSON:
{{
    "intent": "document_update | query | callback_request",
    "aadhaar_status": "submitted | pending | null",
    "bank_status": "submitted | pending | null",
    "rc_status": "submitted | pending | null"
}}

Examples:
"I uploaded Aadhaar" →
{{"aadhaar_status":"submitted"}}

"I will upload later" →
{{"aadhaar_status":"pending"}}
"""

    llm_output = call_llm(prompt)

    try:
        data = json.loads(llm_output)
    except:
        data = {}

    state["updates"] = {}

    if "call" in message.lower():
        state["callback_required"] = True
        state["priority"] = "high"

    if data.get("aadhaar_status"):
        state["updates"]["aadhaar_status"] = data["aadhaar_status"]

    if data.get("bank_status"):
        state["updates"]["bank_status"] = data["bank_status"]

    if data.get("rc_status"):
        state["updates"]["rc_status"] = data["rc_status"]

    state["intent"] = data.get("intent")

    return state

def reconciliation_agent(state):
    lead = state["lead"]
    updates = state["updates"]

    if state.get("callback_required"):
        lead.callback_required = "yes"
        lead.priority = state.get("priority", "medium")

    for key, value in updates.items():
        setattr(lead, key, value)

    return state

def qualification_agent(state):
    lead = state["lead"]

    score = 0

    if lead.aadhaar_status == "submitted":
        score += 30
    if lead.bank_status == "submitted":
        score += 30
    if lead.rc_status == "submitted":
        score += 40

    lead.lead_score = score

    if score == 100:
        lead.onboarding_stage = "completed"
    else:
        lead.onboarding_stage = "in_progress"

    return state

def response_agent(state):
    lead = state["lead"]

    if state.get("callback_required"):
        state["response"] = "Our team will call you shortly 📞"
        return state

    context = {
        "aadhaar": lead.aadhaar_status,
        "bank": lead.bank_status,
        "rc": lead.rc_status,
        "stage": lead.onboarding_stage,
        "score": lead.lead_score
    }

    channel = state.get("channel", "whatsapp")
    history = get_history(lead.lead_id)

    prompt = f"""
    You are an onboarding assistant.

    Lead Status:
    {context}

    Conversation History:
    {history}

    Generate a response for {channel}.

    Rules:
    - WhatsApp → short, friendly
    - Email → formal
    - Mention missing documents
    - Appreciate completed steps
    """

    response = call_llm(prompt)

    state["response"] = response
    return state

def sync_agent(state):
    db = SessionLocal()

    lead = state["lead"]

    db.merge(lead)

    comm = Communication(
        lead_id=lead.lead_id,
        channel=state.get("channel", "unknown"),
        message=state.get("message"),
        timestamp=str(datetime.now())
    )

    db.add(comm)

    db.commit()
    db.close()
    return state

def retrieve_context(lead):
    return f"""
    Aadhaar: {lead.aadhaar_status}
    Bank: {lead.bank_status}
    RC: {lead.rc_status}
    Stage: {lead.onboarding_stage}
    Score: {lead.lead_score}
    """

def get_history(lead_id):
    db = SessionLocal()

    messages = db.query(Communication).filter(
        Communication.lead_id == lead_id
    ).all()

    history = "\n".join([m.message for m in messages[-5:]])

    return history