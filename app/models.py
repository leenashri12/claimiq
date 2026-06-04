from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, Boolean
from datetime import datetime
from app.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, unique=True, index=True)
    member_id = Column(String)
    member_name = Column(String)
    treatment_date = Column(String)
    claim_amount = Column(Float)
    hospital = Column(String, nullable=True)
    cashless_request = Column(Boolean, default=False)
    documents = Column(JSON)

    # Adjudication decision fields
    decision = Column(String, nullable=True)
    approved_amount = Column(Float, nullable=True)
    rejection_reasons = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    audit_trail = Column(JSON, nullable=True)
    deductions = Column(JSON, nullable=True)
    fraud_flags = Column(JSON, nullable=True)
    policy_rules_applied = Column(JSON, nullable=True)
    partial_items_excluded = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    cashless_approved = Column(Boolean, default=False)

    submitted_at = Column(DateTime, default=datetime.utcnow)


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True)
    results = Column(JSON)
    pass_count = Column(Integer)
    fail_count = Column(Integer)
    run_at = Column(DateTime, default=datetime.utcnow)
