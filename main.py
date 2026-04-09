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
def process_message(lead_id: int, message: str):
    db = SessionLocal()

    lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()

    if not lead:
        return {"error": "Lead not found"}

    state = {
        "lead": lead,
        "message": message
    }

    result = graph.invoke(state)

    return {
        "lead_score": lead.lead_score,
        "stage": lead.onboarding_stage,
        "response": result["response"]
    }