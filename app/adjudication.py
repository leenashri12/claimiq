# OPD Claim Adjudication Engine based on policy rules.

import json
import re
from datetime import datetime, date, timedelta
from pathlib import Path

# Policy config values
_BASE_DIR = Path(__file__).parent.parent
POLICY = json.loads((_BASE_DIR / "policy_terms.json").read_text())

EXCLUSIONS = [e.lower() for e in POLICY["exclusions"]]
NETWORK_HOSPITALS = [h.lower() for h in POLICY["network_hospitals"]]

ANNUAL_LIMIT = POLICY["coverage_details"]["annual_limit"]
PER_CLAIM_LIMIT = POLICY["coverage_details"]["per_claim_limit"]
MIN_CLAIM = POLICY["claim_requirements"]["minimum_claim_amount"]
SUBMISSION_DAYS = POLICY["claim_requirements"]["submission_timeline_days"]

COVERAGE = POLICY["coverage_details"]
WAITING_PERIODS = POLICY["waiting_periods"]

# Sub-limits per category
CATEGORY_LIMITS = {
    "consultation": COVERAGE["consultation_fees"]["sub_limit"],
    "diagnostic":   COVERAGE["diagnostic_tests"]["sub_limit"],
    "pharmacy":     COVERAGE["pharmacy"]["sub_limit"],
    "dental":       COVERAGE["dental"]["sub_limit"],
    "vision":       COVERAGE["vision"]["sub_limit"],
    "alternative":  COVERAGE["alternative_medicine"]["sub_limit"],
    "general":      PER_CLAIM_LIMIT,
}

# Doctor registration: KA/45678/2015 or AYUR/KL/2345/2019
DOCTOR_REG_PATTERN = re.compile(r"^[A-Z]{1,8}(/[A-Z]{1,8})?/\d+/\d{4}$")

# Tests requiring pre-authorization
PRE_AUTH_TESTS = ["mri", "ct scan", "ct"]

# Diagnosis-specific waiting periods (days)
DIAGNOSIS_WAITING = {
    "diabetes":         WAITING_PERIODS["specific_ailments"]["diabetes"],
    "type 2 diabetes":  WAITING_PERIODS["specific_ailments"]["diabetes"],
    "type 1 diabetes":  WAITING_PERIODS["specific_ailments"]["diabetes"],
    "hypertension":     WAITING_PERIODS["specific_ailments"]["hypertension"],
    "joint replacement": WAITING_PERIODS["specific_ailments"]["joint_replacement"],
}

# Keywords that trigger exclusion codes
EXCLUSION_KEYWORDS = {
    "teeth whitening":  "COSMETIC_PROCEDURE",   # check longer strings first
    "cosmetic":         "COSMETIC_PROCEDURE",
    "whitening":        "COSMETIC_PROCEDURE",
    "weight loss":      "SERVICE_NOT_COVERED",
    "bariatric":        "SERVICE_NOT_COVERED",
    "infertility":      "SERVICE_NOT_COVERED",
    "experimental":     "EXPERIMENTAL_TREATMENT",
    "adventure sport":  "SERVICE_NOT_COVERED",
}

# Keywords for category detection
DENTAL_KW    = ["tooth", "teeth", "dental", "root canal", "filling", "extraction", "gum"]
VISION_KW    = ["eye", "vision", "optical", "glasses", "contact lens", "lasik"]
ALT_MED_KW   = ["ayurved", "homeopath", "panchakarma", "unani", "naturo"]
PHARMACY_KW  = ["pharmacy", "medicine", "drug", "tablet", "capsule"]
DIAG_KW      = ["mri", "ct scan", "x-ray", "x_ray", "xray", "ultrasound", "ecg", "scan",
                 "blood test", "urine test", "cbc", "lab"]


# Main Adjudication Entrypoint

def adjudicate_claim(
    claim_data: dict,
    previous_claims_same_day: int = 0,
    claims_ytd_amount: float = 0,
) -> dict:
    """Runs the 5-step claim validation pipeline and calculates the approved amount."""
    audit_trail: list = []
    rejection_reasons: list = []
    approved_amount = float(claim_data.get("claim_amount", 0))
    deductions: dict = {}
    partial_items: list = []

    # Step 1: Basic eligibility check
    step1 = _check_eligibility(claim_data)
    audit_trail.append(step1)
    if not step1["passed"]:
        rejection_reasons.extend(step1["rejection_codes"])

    # Step 2: Document validation check
    step2 = _validate_documents(claim_data)
    audit_trail.append(step2)
    if not step2["passed"]:
        rejection_reasons.extend(step2["rejection_codes"])

    # Step 3: Coverage verification (deducts cosmetic exclusions if partial)
    step3 = _verify_coverage(claim_data)
    audit_trail.append(step3)
    if not step3["passed"]:
        rejection_reasons.extend(step3["rejection_codes"])
    if step3.get("partial"):
        approved_amount = step3["approved_amount"]
        partial_items = step3.get("excluded_items", [])

    # Step 4: Category and annual limit validation
    partial_amt = approved_amount if step3.get("partial") else None
    step4 = _validate_limits(claim_data, claims_ytd_amount, partial_amt)
    audit_trail.append(step4)
    if not step4["passed"]:
        rejection_reasons.extend(step4["rejection_codes"])
    else:
        approved_amount = step4["approved_amount"]
        deductions = step4.get("deductions", {})

    # Step 5: Medical necessity check
    step5 = _check_medical_necessity(claim_data)
    audit_trail.append(step5)
    if not step5["passed"]:
        rejection_reasons.extend(step5["rejection_codes"])

    # Run fraud detection checks
    fraud = _check_fraud(claim_data, previous_claims_same_day)

    # Determine final decision status
    unique_rejections = list(dict.fromkeys(rejection_reasons))  # preserve order, dedupe

    if fraud["fraud_detected"]:
        decision = "MANUAL_REVIEW"
        confidence = 0.65
        notes = "Claim flagged for manual review due to suspicious activity patterns."
    elif not unique_rejections:
        if step3.get("partial"):
            decision = "PARTIAL"
            confidence = _partial_confidence(step3)
            notes = f"Claim partially approved. Excluded: {', '.join(partial_items)}."
        else:
            decision = "APPROVED"
            confidence = _approval_confidence(deductions)
            notes = "All adjudication criteria satisfied. Claim approved."
    else:
        # If only coverage produced partial exclusions but other hard failures exist → REJECTED
        decision = "REJECTED"
        confidence = _rejection_confidence(unique_rejections)
        notes = f"Claim rejected: {', '.join(unique_rejections)}."

    if decision in ("REJECTED", "MANUAL_REVIEW"):
        approved_amount = 0.0

    # Collect all policy rules from every step
    all_rules = []
    for step in audit_trail:
        all_rules.extend(step.get("policy_rules", []))
    policy_rules = _deduplicate_rules(all_rules)

    cashless = (
        decision == "APPROVED"
        and bool(claim_data.get("cashless_request"))
        and _is_network_hospital(claim_data.get("hospital", ""))
    )

    return {
        "decision": decision,
        "approved_amount": round(approved_amount, 2),
        "rejection_reasons": unique_rejections,
        "confidence_score": confidence,
        "audit_trail": audit_trail,
        "deductions": deductions,
        "fraud_flags": fraud.get("flags", []),
        "policy_rules_applied": policy_rules,
        "notes": notes,
        "next_steps": _next_steps(decision, unique_rejections),
        "partial_items_excluded": partial_items,
        "cashless_approved": cashless,
    }


# Adjudication Pipeline Step Helper Implementations

def _check_eligibility(claim_data: dict) -> dict:
    """Step 1: Basic Eligibility Check."""
    codes, rules, details = [], [], []

    claim_amount = float(claim_data.get("claim_amount", 0))
    treatment_date_str = claim_data.get("treatment_date", "")
    member_join_date_str = claim_data.get("member_join_date", "")

    # --- Minimum claim amount ---
    if claim_amount < MIN_CLAIM:
        codes.append("BELOW_MIN_AMOUNT")
        rules.append(_rule("Minimum Claim Amount", f"₹{MIN_CLAIM}", f"₹{claim_amount}", "FAILED"))
        details.append(f"Claim ₹{claim_amount} is below the minimum of ₹{MIN_CLAIM}.")
    else:
        rules.append(_rule("Minimum Claim Amount", f"₹{MIN_CLAIM}", f"₹{claim_amount}", "PASSED"))

    # --- Waiting period checks (only when member join date is known) ---
    if member_join_date_str and treatment_date_str:
        try:
            join_date = datetime.strptime(member_join_date_str, "%Y-%m-%d").date()
            treat_date = datetime.strptime(treatment_date_str, "%Y-%m-%d").date()

            # Initial 30-day waiting period
            initial_end = join_date + timedelta(days=WAITING_PERIODS["initial_waiting"])
            if treat_date < initial_end:
                codes.append("WAITING_PERIOD")
                rules.append(_rule(
                    "Initial Waiting Period",
                    f"{WAITING_PERIODS['initial_waiting']} days",
                    f"Treatment on {treatment_date_str} ({(treat_date - join_date).days} days after joining)",
                    "FAILED",
                    f"Eligible from {initial_end}",
                ))
                details.append(
                    f"Treatment falls within the 30-day initial waiting period. Eligible from {initial_end}."
                )
            else:
                rules.append(_rule(
                    "Initial Waiting Period",
                    f"{WAITING_PERIODS['initial_waiting']} days",
                    f"{(treat_date - join_date).days} days since joining",
                    "PASSED",
                ))

            # Diagnosis-specific waiting periods
            documents = claim_data.get("documents", {})
            diagnosis = documents.get("prescription", {}).get("diagnosis", "").lower()

            for condition, wait_days in DIAGNOSIS_WAITING.items():
                if condition in diagnosis:
                    condition_end = join_date + timedelta(days=wait_days)
                    if treat_date < condition_end:
                        codes.append("WAITING_PERIOD")
                        rules.append(_rule(
                            f"Waiting Period – {condition.title()}",
                            f"{wait_days} days",
                            f"Treatment on {treatment_date_str}",
                            "FAILED",
                            f"Eligible from {condition_end}",
                        ))
                        details.append(
                            f"{condition.title()} has a {wait_days}-day waiting period. Eligible from {condition_end}."
                        )
                    else:
                        rules.append(_rule(
                            f"Waiting Period – {condition.title()}",
                            f"{wait_days} days",
                            f"{(treat_date - join_date).days} days since joining",
                            "PASSED",
                        ))
                    break  # Only first match matters

        except ValueError:
            details.append("Could not parse treatment or join date.")

    passed = len(codes) == 0
    return {
        "step": 1,
        "name": "Eligibility Check",
        "passed": passed,
        "rejection_codes": codes,
        "details": details if details else ["All eligibility criteria met."],
        "policy_rules": rules,
    }


def _validate_documents(claim_data: dict) -> dict:
    """Step 2: Document Validation."""
    codes, rules, details = [], [], []
    documents = claim_data.get("documents", {})

    has_prescription = bool(documents.get("prescription"))
    has_bill = bool(documents.get("bill"))

    # --- Prescription ---
    if not has_prescription:
        codes.append("MISSING_DOCUMENTS")
        rules.append(_rule("Prescription", "Mandatory", "Not provided", "FAILED"))
        details.append("Prescription from a registered doctor is missing.")
    else:
        rules.append(_rule("Prescription", "Mandatory", "Provided", "PASSED"))
        prescription = documents["prescription"]

        # Doctor registration number
        doctor_reg = prescription.get("doctor_reg", "").strip()
        if not doctor_reg:
            codes.append("DOCTOR_REG_INVALID")
            rules.append(_rule("Doctor Registration No.", "Required", "Missing", "FAILED"))
            details.append("Doctor registration number is missing from the prescription.")
        elif not DOCTOR_REG_PATTERN.match(doctor_reg.upper()):
            codes.append("DOCTOR_REG_INVALID")
            rules.append(_rule(
                "Doctor Registration Format",
                "STATE/NUMBER/YEAR",
                doctor_reg,
                "FAILED",
            ))
            details.append(f"Invalid doctor registration format: '{doctor_reg}'.")
        else:
            rules.append(_rule("Doctor Registration Format", "STATE/NUMBER/YEAR", doctor_reg, "PASSED"))

    # --- Bill ---
    if not has_bill:
        codes.append("MISSING_DOCUMENTS")
        rules.append(_rule("Medical Bill", "Mandatory", "Not provided", "FAILED"))
        details.append("Medical bill / invoice is missing.")
    else:
        rules.append(_rule("Medical Bill", "Mandatory", "Provided", "PASSED"))

    passed = len(codes) == 0
    return {
        "step": 2,
        "name": "Document Validation",
        "passed": passed,
        "rejection_codes": codes,
        "details": details if details else ["All required documents are valid."],
        "policy_rules": rules,
    }


def _is_pre_auth_required(name: str) -> bool:
    normalized = re.sub(r"[^a-zA-Z0-9]", " ", name.lower())
    words = normalized.split()
    return "mri" in words or "ct" in words

def _verify_coverage(claim_data: dict) -> dict:
    """Step 3: Coverage Verification – detects full rejections and partial approvals."""
    codes, rules, details = [], [], []
    documents = claim_data.get("documents", {})
    prescription = documents.get("prescription", {})
    bill = documents.get("bill", {})

    diagnosis  = prescription.get("diagnosis",  "").lower()
    treatment  = prescription.get("treatment",  "").lower()
    procedures = [p.lower() for p in prescription.get("procedures", [])]
    tests_rx   = [t.lower() for t in prescription.get("tests_prescribed", [])]
    bill_keys  = {k.lower(): v for k, v in bill.items()}

    approved_amount  = float(claim_data.get("claim_amount", 0))
    excluded_items: list = []
    excluded_amount  = 0.0
    partial          = False

    # --- Check diagnosis + treatment for full exclusions ---
    for kw, code in EXCLUSION_KEYWORDS.items():
        if kw in diagnosis or kw in treatment:
            codes.append(code)
            rules.append(_rule("Exclusion Check", f"'{kw}' excluded", diagnosis or treatment, "FAILED"))
            details.append(f"Diagnosis/treatment '{kw}' is excluded from coverage.")
            break  # One hard exclusion is enough to reject

    # --- Check procedures for partial exclusions (e.g. cosmetic in dental visit) ---
    if not codes and procedures:
        for proc in procedures:
            for kw, code in EXCLUSION_KEYWORDS.items():
                if kw in proc:
                    # Find the bill amount for this excluded procedure
                    proc_amount = 0.0
                    for bk, bv in bill_keys.items():
                        kw_slug = kw.replace(" ", "_")
                        proc_slug = proc.replace(" ", "_")
                        if kw_slug in bk or proc_slug in bk:
                            try:
                                proc_amount = float(bv)
                            except (TypeError, ValueError):
                                pass
                            break
                    excluded_items.append(proc)
                    excluded_amount += proc_amount
                    rules.append(_rule("Procedure Coverage", f"'{proc}' excluded ({code})", proc, "FAILED"))
                    details.append(f"Procedure '{proc}' is excluded from coverage.")
                    break

        if excluded_items:
            partial = True
            approved_amount = float(claim_data.get("claim_amount", 0)) - excluded_amount
            rules.append(_rule(
                "Partial Approval",
                f"Excluded items deducted: ₹{excluded_amount}",
                f"Approved: ₹{approved_amount}",
                "PARTIAL",
            ))

    # --- Pre-authorization check ---
    for test in tests_rx:
        if _is_pre_auth_required(test):
            codes.append("PRE_AUTH_MISSING")
            rules.append(_rule("Pre-Authorization", f"Required for {test}", "Not obtained", "FAILED"))
            details.append(f"'{test}' requires pre-authorization before the procedure.")
            break

    # Also check bill keys directly (e.g. bill key = "mri_scan")
    for bk in bill_keys:
        if _is_pre_auth_required(bk) and "PRE_AUTH_MISSING" not in codes:
            codes.append("PRE_AUTH_MISSING")
            rules.append(_rule("Pre-Authorization", f"Required for {bk}", "Not obtained", "FAILED"))
            details.append(f"'{bk}' requires pre-authorization.")
            break

    if not codes and not partial:
        rules.append(_rule("Coverage Check", "Treatment covered", diagnosis or "General", "PASSED"))
        details.append("Treatment/service is covered under the policy.")

    passed = len(codes) == 0
    return {
        "step": 3,
        "name": "Coverage Verification",
        "passed": passed,
        "partial": partial,
        "approved_amount": round(approved_amount, 2),
        "excluded_items": excluded_items,
        "rejection_codes": codes,
        "details": details if details else ["Treatment is covered under policy."],
        "policy_rules": rules,
    }


def _validate_limits(
    claim_data: dict,
    claims_ytd_amount: float = 0,
    partial_amount: float | None = None,
) -> dict:
    """Step 4: Limit Validation with co-payment and network discount."""
    codes, rules, details = [], [], []
    deductions: dict = {}

    base_amount = partial_amount if partial_amount is not None else float(claim_data.get("claim_amount", 0))
    approved_amount = base_amount

    hospital   = claim_data.get("hospital", "")
    is_network = _is_network_hospital(hospital)

    # Detect category and applicable limit
    category         = _detect_category(claim_data)
    applicable_limit = CATEGORY_LIMITS.get(category, PER_CLAIM_LIMIT)

    # --- Per-claim / sub-limit check ---
    if base_amount > applicable_limit:
        limit_label = "Sub-limit" if category != "general" else "Per-Claim Limit"
        code = "SUB_LIMIT_EXCEEDED" if category != "general" else "PER_CLAIM_EXCEEDED"
        codes.append(code)
        rules.append(_rule(
            f"{limit_label} ({category.title()})",
            f"₹{applicable_limit}",
            f"₹{base_amount}",
            "FAILED",
            f"Claim amount exceeds the ₹{applicable_limit} {limit_label.lower()}.",
        ))
        details.append(
            f"Claim amount ₹{base_amount} exceeds the {category} {limit_label.lower()} of ₹{applicable_limit}."
        )
    else:
        rules.append(_rule(
            f"Per-Claim Limit ({category.title()})",
            f"₹{applicable_limit}",
            f"₹{base_amount}",
            "PASSED",
        ))

    # --- Annual limit check ---
    ytd_after = claims_ytd_amount + base_amount
    if ytd_after > ANNUAL_LIMIT:
        codes.append("ANNUAL_LIMIT_EXCEEDED")
        remaining = max(0, ANNUAL_LIMIT - claims_ytd_amount)
        rules.append(_rule("Annual Limit", f"₹{ANNUAL_LIMIT}", f"₹{ytd_after} YTD", "FAILED",
                           f"Remaining balance: ₹{remaining}"))
        details.append(f"Annual limit of ₹{ANNUAL_LIMIT} would be exceeded. Remaining: ₹{remaining}.")
    else:
        rules.append(_rule("Annual Limit", f"₹{ANNUAL_LIMIT}", f"₹{ytd_after} YTD", "PASSED"))

    # --- Deductions (only when no hard limit failure) ---
    if not codes:
        documents = claim_data.get("documents", {})
        bill = documents.get("bill", {})
        has_consultation = any("consult" in k.lower() for k in bill)

        if is_network:
            # Network hospital → 20% discount, no co-pay
            discount = round(approved_amount * 0.20, 2)
            deductions["network_discount"] = discount
            approved_amount -= discount
            rules.append(_rule(
                "Network Discount",
                "20% off (network hospital)",
                f"Rs.{discount} discount applied",
                "APPLIED",
            ))
            details.append(f"Network hospital discount of 20% applied: Rs.{discount} off.")
            if hospital:
                rules.append(_rule("Network Hospital", ", ".join(POLICY["network_hospitals"]), hospital, "CONFIRMED"))
        elif has_consultation and category in ("general", "consultation"):
            # Non-network general/consultation → 10% co-payment
            copay = round(approved_amount * 0.10, 2)
            deductions["copay"] = copay
            approved_amount -= copay
            rules.append(_rule(
                "Co-payment (Consultation)",
                "10% of claim",
                f"Rs.{copay} deducted",
                "APPLIED",
            ))
            details.append(f"10% co-payment applied: Rs.{copay} deducted.")

    passed = len(codes) == 0
    return {
        "step": 4,
        "name": "Limit Validation",
        "passed": passed,
        "rejection_codes": codes,
        "approved_amount": round(approved_amount, 2),
        "deductions": deductions,
        "details": details if details else ["Claim is within all applicable limits."],
        "policy_rules": rules,
    }


def _check_medical_necessity(claim_data: dict) -> dict:
    """Step 5: Medical Necessity Review."""
    codes, rules, details = [], [], []
    documents = claim_data.get("documents", {})
    prescription = documents.get("prescription", {})

    diagnosis = prescription.get("diagnosis", "").strip()
    treatment = prescription.get("treatment", "").strip()
    medicines = prescription.get("medicines_prescribed", [])

    if not diagnosis and not treatment:
        codes.append("NOT_MEDICALLY_NECESSARY")
        rules.append(_rule("Medical Necessity", "Diagnosis required", "Missing", "FAILED"))
        details.append("No diagnosis or treatment information found to establish medical necessity.")
    else:
        condition = diagnosis or treatment
        rules.append(_rule("Medical Necessity", "Diagnosis present", condition, "PASSED"))
        details.append(f"Medical necessity established — Diagnosis: {condition}.")

        if medicines:
            rules.append(_rule(
                "Prescription Medicines",
                "Prescribed by doctor",
                ", ".join(medicines[:3]) + ("…" if len(medicines) > 3 else ""),
                "PASSED",
            ))

    passed = len(codes) == 0
    return {
        "step": 5,
        "name": "Medical Necessity Review",
        "passed": passed,
        "rejection_codes": codes,
        "details": details if details else ["Medical necessity is established."],
        "policy_rules": rules,
    }


# Fraud Detection checks

def _check_fraud(claim_data: dict, previous_claims_same_day: int = 0) -> dict:
    """Detect fraud indicators; triggers MANUAL_REVIEW if found."""
    flags: list = []

    if previous_claims_same_day >= 2:
        flags.append(
            f"Multiple claims ({previous_claims_same_day + 1} total) submitted for the same member on the same day."
        )

    claim_amount = float(claim_data.get("claim_amount", 0))
    if claim_amount > 25000:
        flags.append(f"High-value claim (₹{claim_amount}) requires manual verification.")

    # Unusually high frequency (simple heuristic using previous_claims_same_day)
    if previous_claims_same_day >= 1:
        flags.append("Unusual claim frequency pattern detected.")

    return {"fraud_detected": len(flags) > 0, "flags": flags}


# Internal utility functions

def _detect_category(claim_data: dict) -> str:
    """Detect claim category to apply the right sub-limit."""
    documents = claim_data.get("documents", {})
    prescription = documents.get("prescription", {})
    bill = documents.get("bill", {})

    text_corpus = " ".join([
        prescription.get("diagnosis", ""),
        prescription.get("treatment", ""),
        " ".join(prescription.get("procedures", [])),
        " ".join(bill.keys()),
    ]).lower()

    if any(kw in text_corpus for kw in DENTAL_KW):
        return "dental"
    if any(kw in text_corpus for kw in VISION_KW):
        return "vision"
    if any(kw in text_corpus for kw in ALT_MED_KW):
        return "alternative"
    if any(kw in text_corpus for kw in DIAG_KW):
        return "diagnostic"

    # If the bill only has pharmacy items
    bill_keys_lower = [k.lower() for k in bill.keys()]
    if all(any(pk in k for pk in PHARMACY_KW) for k in bill_keys_lower) and bill_keys_lower:
        return "pharmacy"

    return "general"


def _is_network_hospital(hospital: str) -> bool:
    return bool(hospital) and hospital.lower() in NETWORK_HOSPITALS


def _rule(name: str, value: str, claim_value: str, result: str, note: str = "") -> dict:
    entry = {"rule": name, "policy_value": value, "claim_value": claim_value, "result": result}
    if note:
        entry["note"] = note
    return entry


def _deduplicate_rules(rules: list) -> list:
    seen, out = set(), []
    for r in rules:
        key = r["rule"]
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _approval_confidence(deductions: dict) -> float:
    return 0.93 if deductions else 0.95


def _partial_confidence(step3: dict) -> float:
    return 0.90


def _rejection_confidence(reasons: list) -> float:
    hard = {"PER_CLAIM_EXCEEDED", "SUB_LIMIT_EXCEEDED", "MISSING_DOCUMENTS",
            "WAITING_PERIOD", "SERVICE_NOT_COVERED", "PRE_AUTH_MISSING", "BELOW_MIN_AMOUNT"}
    if any(r in hard for r in reasons):
        return 0.96
    return 0.88


def _next_steps(decision: str, reasons: list) -> str:
    if decision == "APPROVED":
        return "Your claim is approved. Payment will be processed within 3–5 business days."
    if decision == "PARTIAL":
        return (
            "Your claim is partially approved. Payment for approved items will be processed "
            "within 3–5 business days. Excluded items can be appealed within 30 days."
        )
    if decision == "MANUAL_REVIEW":
        return (
            "Your claim has been flagged for manual review. A claims officer will contact "
            "you within 2 business days to discuss next steps."
        )
    # REJECTED
    reasons_str = ", ".join(reasons) if reasons else "policy non-compliance"
    return (
        f"Claim rejected due to: {reasons_str}. "
        "Please contact support or file an appeal within 30 days with supporting documents."
    )
