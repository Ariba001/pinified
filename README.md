The system uses:

    -LangGraph for agent workflow orchestration
    -LLM (Groq) for understanding and response generation
    -RAG (Chroma) for context-aware responses
    -FastAPI for API interaction

---------------------------------------------------------------------------------

How to Run - 

1️. Clone the repo - 

git clone https://github.com/Ariba001/pinified.git
cd pinified

2️. Create virtual environment -
python -m venv venv
venv\Scripts\activate

3️. Install dependencies - 
pip install -r requirements.txt

4️. Run FastAPI server - 
uvicorn main:app --reload

5. Open API docs
http://127.0.0.1:8000/docs

6. create .env file in repo and create free api key from this website "https://console.groq.com/home" for llm 
GROQ_API_KEY=your_api_key

-----------------------------------------------------------------------------------

System Architecture - 

CSV Upload → Ingestion Agent → Database (Source of Truth)
                                         ↓
                                  FastAPI API Layer
                                         ↓
                                 LangGraph Workflow
                                         ↓
   RAG → Understanding → Reconciliation → Qualification → Sync → Response
                                         ↓
                      Structured Output + Communication Drafts

----------------------------------------------------------------------------------

Database Schema - 

1.Lead Table -
lead_id
name, phone, email
aadhaar_status, bank_status, rc_status
onboarding_stage
lead_score
preferred_channel
callback_required, priority

2.Communication Table - 
id
lead_id
channel
message
timestamp

-----------------------------------------------------------------------------------

Sample csv input - 

name,phone,email,city,vehicle_type,vehicle_count,aadhaar_status,bank_status,rc_status
Ali,9876543210,ali@email.com,Delhi,Truck,2,pending,pending,pending
Sara,9876543211,sara@email.com,Mumbai,Van,1,submitted,pending,pending

-----------------------------------------------------------------------------------

sample inputs - 

whatsapp message - uploaded aadhaar
email message - I have submitted my bank documents
callback request - Call me later

------------------------------------------------------------------------------------

sample output - 

{
  "lead_score": 60,
  "onboarding_stage": "in_progress",
  "missing_fields": ["bank", "rc"],
  "preferred_channel": "whatsapp",
  "latest_update_source": "whatsapp",
  "extracted_information": {
    "aadhaar_status": "submitted"
  },
  "next_best_action": "Collect missing documents",
  "whatsapp_draft": "Great! Aadhaar received . Please upload Bank and RC.",
  "email_draft": "Dear user, your Aadhaar has been received. Kindly submit Bank and RC documents.",
  "callback_required": false,
  "priority": "low",
  "updated_database_state": {
    "aadhaar": "submitted",
    "bank": "pending",
    "rc": "pending"
  }
}

----------------------------------------------------------------------------------------------------------

Agent Logic - 

Understanding Agent Prompt - 
Extracts structured JSON from user message
Handles variations like “adhaar” vs “aadhaar”

Response Agent Logic - 
Uses structured inputs:
Acknowledged documents
Missing documents
Prevents hallucination using strict rules

------------------------------------------------------------------------------------------------------------

