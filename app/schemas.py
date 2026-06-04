from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ClaimSubmit(BaseModel):
    """Schema for submitting a new claim."""
    member_id: str
    member_name: str
    treatment_date: str  # YYYY-MM-DD format
    claim_amount: float
    hospital: Optional[str] = None
    cashless_request: Optional[bool] = False
    member_join_date: Optional[str] = None   # YYYY-MM-DD; used for waiting period checks
    previous_claims_same_day: Optional[int] = 0
    documents: Dict[str, Any] = {}  # Flexible: {prescription: {...}, bill: {...}, ...}


class AuditStep(BaseModel):
    step: int
    name: str
    passed: bool
    rejection_codes: List[str]
    details: List[str]
    policy_rules: List[Dict[str, Any]]


class AdjudicationResult(BaseModel):
    decision: str
    approved_amount: float
    rejection_reasons: List[str]
    confidence_score: float
    audit_trail: List[Dict[str, Any]]
    deductions: Dict[str, float]
    fraud_flags: List[str]
    policy_rules_applied: List[Dict[str, Any]]
    notes: str
    next_steps: str
    partial_items_excluded: List[str]
    cashless_approved: bool


class ClaimResponse(BaseModel):
    claim_id: str
    result: Dict[str, Any]
