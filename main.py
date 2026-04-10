from fastapi import FastAPI
from database import SessionLocal
from models import Lead
from graph import build_graph
from fastapi import UploadFile, File
import shutil
from agents import ingestion_agent

app = FastAPI()
graph = build_graph()

@app.post("/create_lead")

def create_lead(name: str, phone: int):
    db = SessionLocal()

    lead = Lead(name=name, phone=phone)
    db.add(lead)
    db.commit()

    return {"message": "Lead created", "lead_id": lead.lead_id}

@app.post("/upload_csv")
def upload_csv(file: UploadFile = File(...)):

    file_path = f"data/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = ingestion_agent(file_path)

    return {
        "message": "File processed",
        "details": result
    }

@app.post("/message/{lead_id}")
def process_message(lead_id: int, message: str, channel: str = "whatsapp/email"):
    db = SessionLocal()
    lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()

    state = {
        "lead": lead,
        "message": message,
        "channel": channel
    }

    result = graph.invoke(state)

    missing_fields = []

    if lead.aadhaar_status != "submitted":
        missing_fields.append("aadhaar")
    if lead.bank_status != "submitted":
        missing_fields.append("bank")
    if lead.rc_status != "submitted":
        missing_fields.append("rc")

    output = {
        "lead_score": lead.lead_score,
        "onboarding_stage": lead.onboarding_stage,
        "missing_fields": missing_fields,
        "preferred_channel": lead.preferred_channel,
        "latest_update_source": channel,
        "extracted_information": state.get("updates", {}),
        "next_best_action": "Collect missing documents" if missing_fields else "Onboarding complete",
        "whatsapp_draft": result.get("whatsapp_response"),
        "email_draft": result.get("email_response"),
        "callback_required": state.get("callback_required", False),
        "priority": state.get("priority", "low"),
        "updated_database_state": {
            "aadhaar": lead.aadhaar_status,
            "bank": lead.bank_status,
            "rc": lead.rc_status
        }
    }

    return output