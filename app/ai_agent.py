"""
AI Agent — Gemini Integration (google-genai SDK)

Features:
  1. Document Extraction  — Extract structured data from uploaded prescription/bill images or PDFs
  2. Claim Analysis        — Enrich adjudication with AI confidence, medical necessity, fraud detection

Falls back gracefully if the API key is missing or a call fails.

SDK: google-genai (official SDK)
Docs: https://ai.google.dev/gemini-api/docs/quickstart?lang=python
"""

import os
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
VISION_MODEL = "gemini-2.0-flash"      # Primary vision model (verified available)
TEXT_MODEL   = "gemini-2.0-flash-lite" # For text-only claim analysis (lighter quota)


# ===========================================================================
# 1. Document Extraction (Vision)
# ===========================================================================

def extract_document_data(file_bytes: bytes, mime_type: str, doc_type: str = "auto") -> dict:
    """
    Send an uploaded image or PDF to Gemini Vision and extract structured
    medical document data.

    Args:
        file_bytes: Raw bytes of the uploaded file
        mime_type:  e.g. 'image/jpeg', 'image/png', 'application/pdf'
        doc_type:   'prescription', 'bill', or 'auto' (let AI decide)

    Returns:
        {
          "success": True/False,
          "document_type": "prescription" | "bill" | "report",
          "extracted_data": { ... structured fields ... },
          "raw_text": "...",
          "confidence": 0.0-1.0,
          "notes": "..."
        }
    """
    if not GOOGLE_API_KEY:
        return {
            "success": False,
            "error": "No Gemini API key configured. Add GOOGLE_API_KEY to your .env file.",
            "extracted_data": {},
        }

    # ── Model fallback chain ──────────────────────────────────────────────────
    # These are verified-available models for this API key (vision-capable).
    # On 429 quota error we silently try the next model in the chain.
    # Primary: gemini-2.0-flash  →  Fallback 1: gemini-2.0-flash-lite  →  Fallback 2: gemini-2.5-flash
    vision_model_chain = [
        "gemini-2.0-flash",       # Primary — best speed/quality balance
        "gemini-2.0-flash-lite",  # Lighter version, separate quota pool
        "gemini-2.5-flash",       # Most capable — use if others are rate-limited
    ]

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GOOGLE_API_KEY)
    prompt = _build_extraction_prompt(doc_type)

    last_error = None
    quota_exhausted = False

    for model_name in vision_model_chain:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    prompt,
                ],
            )

            raw = response.text.strip()

            # Strip markdown fences if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw)

            return {
                "success":        True,
                "document_type":  parsed.get("document_type", doc_type),
                "extracted_data": parsed.get("extracted_data", {}),
                "raw_text":       parsed.get("raw_text", ""),
                "confidence":     float(parsed.get("extraction_confidence", 0.85)),
                "notes":          parsed.get("notes", ""),
                "ai_model":       model_name,
            }

        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Gemini returned an unexpected response format. Please try again.",
                "extracted_data": {},
            }

        except Exception as exc:
            err_str = str(exc)
            # Detect quota / rate-limit / transient service errors (429, 503, 500, UNAVAILABLE, etc.) — try next model silently
            is_transient = (
                "429" in err_str
                or "503" in err_str
                or "500" in err_str
                or "RESOURCE_EXHAUSTED" in err_str
                or "UNAVAILABLE" in err_str
                or "quota" in err_str.lower()
                or "high demand" in err_str.lower()
                or "overloaded" in err_str.lower()
            )
            if is_transient:
                last_error = exc
                quota_exhausted = True
                continue  # try next model in the chain
            # Any other error → return immediately with a clean message
            return {
                "success": False,
                "error": f"Document extraction failed: {err_str[:200]}",
                "extracted_data": {},
            }

    # All models exhausted or unavailable
    if quota_exhausted:
        return {
            "success": False,
            "error": (
                f"Gemini API is currently overloaded or quota exceeded. "
                f"Details: {str(last_error)[:150]}. "
                "Please retry in a few minutes, check your quota at https://aistudio.google.com, "
                "or try another document."
            ),
            "extracted_data": {},
        }

    return {
        "success": False,
        "error": f"Document extraction failed: {str(last_error)[:200]}",
        "extracted_data": {},
    }


def _build_extraction_prompt(doc_type: str) -> str:
    return f"""You are an expert medical document data extractor for an Indian OPD insurance system.
Analyze this medical document image/PDF and extract ALL relevant information.

The document type hint is: "{doc_type}" (if "auto", determine the type yourself).

Respond ONLY with a valid JSON object in this exact structure:

{{
  "document_type": "prescription" or "bill" or "diagnostic_report" or "pharmacy_bill",
  "extraction_confidence": <float 0.0 to 1.0>,
  "raw_text": "<full text content you can read from the document>",
  "notes": "<any issues: blurry areas, unclear text, handwriting quality>",
  "extracted_data": {{
    "patient_name": "<full patient name if visible>",
    "member_id": "<employee/member ID like EMP001 or MEM-001 if visible, else empty string>",
    "treatment_date": "<MUST be in YYYY-MM-DD format. Convert any date format (01-Nov-2024, 1/11/2024, November 1 2024) to YYYY-MM-DD>",
    "doctor_name": "<doctor name including title e.g. Dr. Rajan Sharma>",
    "doctor_registration": "<registration number in STATE/NUMBER/YEAR format if visible, e.g. KA/45678/2015>",
    "hospital_name": "<hospital or clinic name if visible>",
    "diagnosis": "<diagnosis or chief complaint>",
    "treatment": "<treatment or procedure name if applicable>",
    "medicines_prescribed": ["<medicine 1>", "<medicine 2>"],
    "tests_prescribed": ["<test 1>", "<test 2>"],
    "procedures": ["<procedure 1>"],
    "bill_items": {{
      "<item_name_snake_case>": <amount_as_number>,
      "<item_name_snake_case>": <amount_as_number>
    }},
    "total_amount": <total bill amount as number if visible>,
    "doctor_signature_present": true or false,
    "hospital_stamp_present": true or false
  }}
}}

Critical rules:
- member_id: Look for labels like "Member ID", "Employee ID", "EMP No.", "Patient ID" and extract the value (e.g. "EMP001").
- treatment_date: ALWAYS convert to YYYY-MM-DD. Examples: "01-Nov-2024" -> "2024-11-01", "15/10/2024" -> "2024-10-15".
- For bill_items, use snake_case keys like "consultation_fee", "medicines", "diagnostic_tests", "mri_scan".
- Leave fields as empty string "" or empty list [] if not found in the document.
- If the document is a bill, focus on extracting line items and amounts.
- If the document is a prescription, focus on doctor info, diagnosis, and medicines.
- For doctor registration, identify the STATE/NUMBER/YEAR pattern (e.g. KA/45678/2015, MH/23456/2018).
- Set extraction_confidence lower if text is blurry, handwritten, or partially visible.
"""


# ===========================================================================
# 2. Claim Analysis (Text-only AI enrichment)
# ===========================================================================

def analyze_claim_with_ai(claim_data: dict) -> dict:
    """
    Send claim context to Gemini for an AI-powered review.

    Returns a dict with:
        confidence (float 0-1), medical_necessity_justified (bool),
        fraud_indicators (list[str]), notes (str), ai_powered (bool)

    Falls back to safe defaults if the API is unavailable.
    """
    if not GOOGLE_API_KEY:
        return _fallback_result("No API key configured — using rule-based defaults.")

    try:
        from google import genai

        client = genai.Client(api_key=GOOGLE_API_KEY)

        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=_build_analysis_prompt(claim_data),
        )

        raw = response.text.strip()

        # Strip markdown code fences
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        parsed = json.loads(raw)

        return {
            "confidence":                  float(parsed.get("confidence", 0.80)),
            "medical_necessity_justified": bool(parsed.get("medical_necessity_justified", True)),
            "fraud_indicators":            parsed.get("fraud_indicators", []),
            "notes":                       parsed.get("notes", ""),
            "ai_powered":                  True,
        }

    except Exception as exc:
        return _fallback_result(f"AI analysis unavailable: {str(exc)[:150]}")


def _build_analysis_prompt(claim_data: dict) -> str:
    return f"""You are an expert OPD insurance claims adjudicator for an Indian health insurer.
Analyze the following claim and respond ONLY with a valid JSON object — no extra text.

Claim Data:
{json.dumps(claim_data, indent=2, default=str)}

Respond strictly in this JSON format:
{{
  "confidence": <float 0.0 to 1.0 reflecting the claim's legitimacy>,
  "medical_necessity_justified": <true or false>,
  "fraud_indicators": ["<description of any suspicious pattern>"],
  "notes": "<brief 1-2 sentence assessment>"
}}

Scoring guidelines:
- confidence > 0.90  means very likely legitimate
- confidence < 0.70  means suspicious, recommend manual review
- Set medical_necessity_justified = false ONLY if the diagnosis clearly does not justify the treatment
- Flag fraud if: multiple claims same day, unusually high amount, or diagnosis does not match age/gender
"""


def _fallback_result(reason: str) -> dict:
    return {
        "confidence":                  0.80,
        "medical_necessity_justified": True,
        "fraud_indicators":            [],
        "notes":                       reason,
        "ai_powered":                  False,
    }
