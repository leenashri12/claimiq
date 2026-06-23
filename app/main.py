# FastAPI application routing and API endpoints

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models
from app.database import engine, get_db
from app.schemas import ClaimSubmit, ClaimResponse
from app.adjudication import adjudicate_claim
from app.ai_agent import analyze_claim_with_ai, extract_document_data

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# Load configuration and test data from JSON files
_BASE = Path(__file__).parent.parent
POLICY     = json.loads((_BASE / "policy_terms.json").read_text())
TEST_CASES = json.loads((_BASE / "test_cases.json").read_text())["test_cases"]

# Initialize FastAPI app
app = FastAPI(
    title="ClaimIQ OPD Claim Adjudication Tool",
    description="AI-powered OPD insurance claim adjudication system",
    version="1.0.0",
)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=str(_BASE / "app" / "static")), name="static")


# Serve frontend SPA

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(str(_BASE / "app" / "static" / "index.html"))


# Document OCR extraction using Gemini Vision

ALLOWED_MIME = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif",
    "application/pdf",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post("/api/extract-document", tags=["Document Processing"])
async def extract_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default="auto"),
):
    """
    Upload a medical document image or PDF.
    Gemini Vision will extract structured data (doctor info, diagnosis,
    medicines, bill items) and return it as JSON.

    Supported formats: JPEG, PNG, WebP, GIF, PDF
    Max size: 10 MB
    """
    # Validate mime type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. Allowed: {', '.join(sorted(ALLOWED_MIME))}",
        )

    # Read file bytes
    file_bytes = await file.read()

    # Validate size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). Max: 10 MB.",
        )

    # Send to Gemini Vision
    result = extract_document_data(file_bytes, content_type, doc_type)

    return {
        "filename":  file.filename,
        "mime_type": content_type,
        "size_kb":   round(len(file_bytes) / 1024, 1),
        **result,
    }


# Policy terms retrieval

@app.get("/api/policy", tags=["Policy"])
async def get_policy():
    """Return the full policy terms document."""
    return POLICY


# Aggregate stats for dashboard cards

@app.get("/api/stats", tags=["Dashboard"])
async def get_stats(db: Session = Depends(get_db)):
    """Return aggregate statistics for the dashboard."""
    claims = db.query(models.Claim).all()
    total    = len(claims)
    approved = sum(1 for c in claims if c.decision == "APPROVED")
    rejected = sum(1 for c in claims if c.decision == "REJECTED")
    partial  = sum(1 for c in claims if c.decision == "PARTIAL")
    manual   = sum(1 for c in claims if c.decision == "MANUAL_REVIEW")
    total_approved_amt = sum(
        (c.approved_amount or 0)
        for c in claims
        if c.decision in ("APPROVED", "PARTIAL")
    )
    avg_confidence = (
        sum(c.confidence_score or 0 for c in claims) / total if total else 0
    )
    return {
        "total_claims":              total,
        "approved":                  approved,
        "rejected":                  rejected,
        "partial":                   partial,
        "manual_review":             manual,
        "approval_rate":             round(approved / total * 100, 1) if total else 0,
        "successful_adjudications":  approved + partial,
        "success_rate":              round((approved + partial) / total * 100, 1) if total else 0,
        "total_approved_amount":     round(total_approved_amt, 2),
        "avg_confidence":            round(avg_confidence * 100, 1),
    }


# Claim submission and listing endpoints

@app.post("/api/claims", tags=["Claims"])
async def submit_claim(claim: ClaimSubmit, db: Session = Depends(get_db)):
    """Submit a new OPD claim and return the adjudication result."""
    claim_id   = f"CLM_{uuid.uuid4().hex[:6].upper()}"
    claim_dict = claim.model_dump()

    # ---- AI enrichment ----
    ai_result = analyze_claim_with_ai(claim_dict)

    # ---- Rule-based adjudication ----
    result = adjudicate_claim(
        claim_dict,
        previous_claims_same_day=claim_dict.get("previous_claims_same_day", 0),
        claims_ytd_amount=0,
    )

    # Blend confidence ONLY when Gemini actually ran (not fallback defaults).
    # This keeps the New Claim confidence consistent with the Test Runner,
    # which uses pure rule-based scores.
    if ai_result.get("ai_powered", False):
        result["confidence_score"] = round(
            (result["confidence_score"] + ai_result["confidence"]) / 2, 2
        )
    # else: keep the pure rule-based confidence score unchanged

    result["ai_notes"]   = ai_result.get("notes", "")
    result["ai_powered"] = ai_result.get("ai_powered", False)


    # ---- Persist ----
    db_claim = models.Claim(
        claim_id              = claim_id,
        member_id             = claim_dict.get("member_id", ""),
        member_name           = claim_dict.get("member_name", ""),
        treatment_date        = claim_dict.get("treatment_date", ""),
        claim_amount          = float(claim_dict.get("claim_amount", 0)),
        hospital              = claim_dict.get("hospital"),
        cashless_request      = bool(claim_dict.get("cashless_request")),
        documents             = claim_dict.get("documents", {}),
        decision              = result["decision"],
        approved_amount       = result["approved_amount"],
        rejection_reasons     = result["rejection_reasons"],
        confidence_score      = result["confidence_score"],
        audit_trail           = result["audit_trail"],
        deductions            = result["deductions"],
        fraud_flags           = result.get("fraud_flags", []),
        policy_rules_applied  = result["policy_rules_applied"],
        partial_items_excluded= result.get("partial_items_excluded", []),
        notes                 = result["notes"],
        next_steps            = result["next_steps"],
        cashless_approved     = result.get("cashless_approved", False),
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)

    return {"claim_id": claim_id, "result": result}


@app.get("/api/claims", tags=["Claims"])
async def list_claims(db: Session = Depends(get_db)):
    """Return all submitted claims ordered by submission date descending."""
    claims = (
        db.query(models.Claim)
        .order_by(models.Claim.submitted_at.desc())
        .all()
    )
    return [_serialize_claim(c) for c in claims]


@app.get("/api/claims/{claim_id}", tags=["Claims"])
async def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """Return full details of a specific claim."""
    claim = (
        db.query(models.Claim)
        .filter(models.Claim.claim_id == claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")
    return _serialize_claim(claim)


# UI Test suite runner

@app.post("/api/test-runner/run-all", tags=["Testing"])
async def run_all_tests(db: Session = Depends(get_db)):
    """Run all 10 provided test cases and compare with expected outputs."""
    results = []

    for tc in TEST_CASES:
        input_data = tc["input_data"]
        expected   = tc["expected_output"]

        result = adjudicate_claim(
            input_data,
            previous_claims_same_day=input_data.get("previous_claims_same_day", 0),
            claims_ytd_amount=0,
        )

        exp_decision = expected.get("decision", "")
        act_decision = result["decision"]
        decision_ok  = act_decision == exp_decision

        exp_amount   = expected.get("approved_amount")
        act_amount   = result.get("approved_amount")
        amount_ok    = True
        if exp_amount is not None and act_amount is not None:
            amount_ok = abs(float(exp_amount) - float(act_amount)) <= 150

        passed = decision_ok and amount_ok

        results.append({
            "case_id":          tc["case_id"],
            "case_name":        tc["case_name"],
            "description":      tc.get("description", ""),
            "passed":           passed,
            "expected_decision": exp_decision,
            "actual_decision":  act_decision,
            "decision_match":   decision_ok,
            "expected_amount":  exp_amount,
            "actual_amount":    act_amount,
            "amount_match":     amount_ok,
            "confidence_score": result.get("confidence_score"),
            "rejection_reasons": result.get("rejection_reasons", []),
            "audit_trail":      result.get("audit_trail", []),
            "policy_rules":     result.get("policy_rules_applied", []),
        })

    pass_count = sum(1 for r in results if r["passed"])
    fail_count = len(results) - pass_count
    run_id     = f"RUN_{uuid.uuid4().hex[:6].upper()}"

    # Persist test run
    test_run = models.TestRun(
        run_id     = run_id,
        results    = results,
        pass_count = pass_count,
        fail_count = fail_count,
    )
    db.add(test_run)
    db.commit()

    return {
        "run_id":    run_id,
        "total":     len(results),
        "passed":    pass_count,
        "failed":    fail_count,
        "pass_rate": round(pass_count / len(results) * 100, 1),
        "results":   results,
    }


# Helper to serialize DB Claim objects

def _serialize_claim(c: models.Claim) -> dict:
    return {
        "claim_id":             c.claim_id,
        "member_id":            c.member_id,
        "member_name":          c.member_name,
        "treatment_date":       c.treatment_date,
        "claim_amount":         c.claim_amount,
        "hospital":             c.hospital,
        "cashless_request":     c.cashless_request,
        "documents":            c.documents,
        "decision":             c.decision,
        "approved_amount":      c.approved_amount,
        "rejection_reasons":    c.rejection_reasons,
        "confidence_score":     c.confidence_score,
        "audit_trail":          c.audit_trail,
        "deductions":           c.deductions,
        "fraud_flags":          c.fraud_flags,
        "policy_rules_applied": c.policy_rules_applied,
        "partial_items_excluded": c.partial_items_excluded,
        "notes":                c.notes,
        "next_steps":           c.next_steps,
        "cashless_approved":    c.cashless_approved,
        "submitted_at":         c.submitted_at.isoformat() if c.submitted_at else None,
    }
