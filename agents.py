from database import SessionLocal
import pandas as pd
from datetime import datetime
from models import Lead, Communication
import json
from llm import call_llm
from vectordb import store_message
from vectordb import retrieve_similar
from whatsapp import send_whatsapp
from email_service import send_email
from score import calculate_score

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
    message = state["message"].lower()
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

Rules:
- "uploaded", "submitted", "done" → submitted
- "not uploaded", "missing" → pending
- If not mentioned → null
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

    updates = {}

    if "aadhaar" in message or "adhaar" in message:
        if "upload" in message or "submitted" in message:
            updates["aadhaar_status"] = "submitted"

    if "bank" in message:
        if "upload" in message:
            updates["bank_status"] = "submitted"

    if "rc" in message:
        if "upload" in message:
            updates["rc_status"] = "submitted"

    print("UPDATES:", updates)

    state["updates"] = updates

    state["intent"] = data.get("intent")

    return state

def reconciliation_agent(state):
    lead = state["lead"]
    updates = state["updates"]

    if state.get("callback_required"):
        lead.callback_required = "yes"
        lead.priority = state.get("priority", "medium")

    print("BEFORE:", lead.aadhaar_status)

    for key, value in updates.items():
        setattr(lead, key, value)

    print("AFTER:", lead.aadhaar_status)
    return state

def qualification_agent(state):
    lead = state["lead"]

    score = calculate_score(lead)
    lead.lead_score = score

    if score == 100:
        lead.onboarding_stage = "completed"
    else:
        lead.onboarding_stage = "in_progress"

    return state

def response_agent(state):
    lead = state["lead"]
    channel = state.get("channel", "whatsapp")
    history = get_history(lead.lead_id)

    acknowledged = []
    missing = []

    if lead.aadhaar_status == "submitted":
        acknowledged.append("Aadhaar")
    else:
        missing.append("Aadhaar")

    if lead.bank_status == "submitted":
        acknowledged.append("Bank")
    else:
        missing.append("Bank")

    if lead.rc_status == "submitted":
        acknowledged.append("RC")
    else:
        missing.append("RC")

    context = f"""
    Aadhaar: {lead.aadhaar_status}
    Bank: {lead.bank_status}
    RC: {lead.rc_status}
    Stage: {lead.onboarding_stage}
    Score: {lead.lead_score}
    """

    prompt = f"""
    You are an onboarding assistant.

    Lead Status:
    {context}

    Acknowledged Documents: {acknowledged}
    Missing Documents: {missing}

    Conversation History:
    {history}

    STRICT RULES:
    - Only mention documents in Acknowledged list
    - Only ask for documents in Missing list
    - Do NOT confuse Aadhaar, Bank, RC
    - Do NOT assume anything

    Style:
    - WhatsApp → short, friendly
    - Email → formal

    Generate response for {channel}.
    """

    if state.get("callback_required"):
        response = "Our team will call you shortly to assist you further."
    else:
        response = call_llm(prompt)

    whatsapp_prompt = prompt + "\nGenerate ONLY WhatsApp message."
    whatsapp_response = call_llm(whatsapp_prompt)

    email_prompt = prompt + "\nGenerate ONLY Email message."
    email_response = call_llm(email_prompt)

    state["whatsapp_response"] = whatsapp_response
    state["email_response"] = email_response

    if channel == "whatsapp":
        send_whatsapp(lead.phone, whatsapp_response)

    elif channel == "email":
        send_email(lead.email, "Onboarding Update", email_response)

    print("FINAL CONTEXT:", context)
    print("ACKNOWLEDGED:", acknowledged)
    print("MISSING:", missing)

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
    store_message(lead.lead_id, state["message"])
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

def get_rag_context(state):
    lead = state["lead"]
    query = state["message"]

    similar_msgs = retrieve_similar(lead.lead_id, query)

    return "\n".join(similar_msgs[0]) if similar_msgs else ""