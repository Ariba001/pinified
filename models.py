from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class Lead(Base):
    __tablename__ = "leads"

    lead_id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    phone = Column(String)
    email = Column(String)
    city = Column(String)

    vehicle_type = Column(String)
    vehicle_count = Column(Integer)

    aadhaar_status = Column(String, default="pending")
    bank_status = Column(String, default="pending")
    rc_status = Column(String, default="pending")

    app_installed = Column(String, default="no")
    preferred_channel = Column(String)

    onboarding_stage = Column(String, default="new")
    lead_score = Column(Integer, default=0)

class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.lead_id"))
    channel = Column(String)
    message = Column(String)
    timestamp = Column(String)
    callback_required = Column(String, default="no")
    priority = Column(String, default="low")