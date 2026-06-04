"""
gen_rejection_doc.py
Generates a realistic PDF whose adjudication will be REJECTED.

Rejection triggers:
  1. INVALID_DOCTOR_REG  -- doctor reg format is wrong (not STATE/NUMBER/YEAR)
  2. POLICY_EXCLUDED_TREATMENT -- "Weight loss treatments" is in exclusions list
  3. claim_amount (Rs. 7,500) exceeds per-claim sub-limit for the category

File: sample_documents/rejected_weight_loss_claim.pdf
"""

from fpdf import FPDF
from pathlib import Path

OUT = Path("sample_documents")
OUT.mkdir(exist_ok=True)

BLU = (30, 58, 138)
LBL = (230, 236, 255)
GRN = (0, 130, 0)
RED = (180, 30, 30)
ORG = (180, 90, 0)
GRY = (80, 80, 80)


def new_pdf(title, sub):
    class Doc(FPDF):
        def header(self):
            self.set_fill_color(140, 30, 30)      # dark red banner (signals risky clinic)
            self.rect(0, 0, 210, 30, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 14)
            self.set_xy(0, 5)
            self.cell(210, 8, title, align="C", ln=True)
            self.set_font("Helvetica", "", 8)
            self.cell(210, 6, sub, align="C", ln=True)
            self.set_text_color(0, 0, 0)
            self.ln(4)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(140, 140, 140)
            self.cell(0, 5,
                "Computer-generated document. Valid for insurance/reimbursement purposes.",
                align="C")
            self.set_text_color(0, 0, 0)

    doc = Doc()
    doc.set_margins(14, 14, 14)
    doc.set_auto_page_break(True, 16)
    doc.add_page()
    return doc


def sec(pdf, text):
    pdf.set_fill_color(*LBL)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BLU)
    pdf.cell(0, 7, "  " + text, fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def kv(pdf, label, value, lw=58):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GRY)
    pdf.cell(lw, 6, label + ":")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, str(value), ln=True)


def divider(pdf):
    pdf.set_draw_color(200, 200, 200)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.ln(2)


def thead(pdf, cols, widths):
    pdf.set_fill_color(*BLU)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    for col, w in zip(cols, widths):
        pdf.cell(w, 7, col, fill=True, align="C")
    pdf.ln()
    pdf.set_text_color(0, 0, 0)


def trow(pdf, vals, widths, shade=False):
    pdf.set_fill_color(245, 247, 255) if shade else pdf.set_fill_color(255, 255, 255)
    pdf.set_font("Helvetica", "", 9)
    for v, w in zip(vals, widths):
        pdf.cell(w, 6, str(v), fill=True)
    pdf.ln()


def gen_rejected_weight_loss():
    pdf = new_pdf(
        "SlimFit Weight Loss & Wellness Centre",
        "Dr. Ramesh Nair (Wellness Consultant)  |  Cert: WLC/2021/RN  "   # <-- INVALID format: not STATE/NUMBER/YEAR
        "|  Plot 44, Indiranagar, Bengaluru-560038  |  Ph: 080-9988-7766"
    )

    # Warning notice box
    pdf.set_fill_color(255, 243, 205)
    pdf.set_text_color(*ORG)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 7,
        "  *** NON-ALLOPATHIC WEIGHT MANAGEMENT PROGRAMME -- Wellness & Lifestyle Clinic ***",
        fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    sec(pdf, "PATIENT DETAILS")
    kv(pdf, "Patient Name",   "Sunita Rao")
    kv(pdf, "Age / Gender",   "36 Years / Female")
    kv(pdf, "Member ID",      "EMP025")
    kv(pdf, "Date of Visit",  "28-Oct-2024")
    kv(pdf, "Programme",      "12-Week Medical Weight Loss Programme")
    pdf.ln(3)

    sec(pdf, "CLINICAL ASSESSMENT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*RED)
    pdf.cell(0, 7, "Chief Complaint: Obesity (BMI 34.2) -- Weight Loss & Body Contouring", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5,
        "Patient presents with obesity (weight: 82 kg, height: 155 cm, BMI: 34.2). "
        "Enrolled in our 12-week medically supervised weight loss programme combining "
        "low-calorie diet, fat-burning injections (Saxenda/Liraglutide), body wrap therapy, "
        "and non-invasive laser fat reduction (cryolipolysis). "
        "No active disease pathology. Goal: reduction of 12-15 kg over the programme.")
    pdf.ln(3)

    sec(pdf, "PROCEDURES & SERVICES")
    thead(pdf, ["#", "Service / Procedure", "Category", "Fee (Rs.)"], [6, 105, 42, 29])
    services = [
        ("1", "Medical Weight Loss Consultation (initial)",  "Consultation",    "1,500"),
        ("2", "Liraglutide (Saxenda) 1.8 mg injection x4",  "Weight Loss Drug", "2,800"),
        ("3", "Body Wrap Detox Therapy (3 sessions)",        "Wellness Spa",    "1,200"),
        ("4", "Cryolipolysis (Laser Fat Reduction) -- trial","Cosmetic/Body",   "2,000"),
        ("5", "Dietary Supplement Pack -- SlimFit Pro",      "Supplement",      "500"),
        ("6", "Metabolic Panel Blood Test",                  "Diagnostic",      "450"),
        ("7", "BMI & Body Composition Analysis",             "Assessment",      "300"),
    ]
    for i, r in enumerate(services):
        trow(pdf, r, [6, 105, 42, 29], shade=(i % 2 == 0))
    pdf.ln(4)

    sec(pdf, "PRESCRIBED ITEMS")
    thead(pdf, ["Item", "Dosage / Instruction", "Duration"], [100, 55, 27])
    items = [
        ("Liraglutide 1.8mg Pen (Saxenda)", "0.6mg SC daily, escalate weekly",  "4 weeks"),
        ("SlimFit Pro Meal Replacement",    "1 sachet per meal (2 meals/day)",   "12 weeks"),
        ("Garcinia Cambogia 800mg (Herbal)","2 caps TDS before meals",           "12 weeks"),
        ("Vitamin B12 1000mcg injection",   "1 amp IM weekly",                  "4 weeks"),
        ("L-Carnitine 500mg tabs",          "1 tab BD on empty stomach",         "8 weeks"),
    ]
    for i, r in enumerate(items):
        trow(pdf, r, [100, 55, 27], shade=(i % 2 == 0))
    pdf.ln(4)

    sec(pdf, "BILL SUMMARY")
    line_items = [
        ("Medical Weight Loss Consultation",   "1,500"),
        ("Liraglutide (Saxenda) Injections",   "2,800"),
        ("Body Wrap Detox Therapy",            "1,200"),
        ("Cryolipolysis Fat Reduction",        "2,000"),
        ("Dietary Supplement Pack",            "500"),
        ("Metabolic Panel Blood Test",         "450"),
        ("BMI & Body Composition Analysis",    "300"),
    ]
    for lbl, amt in line_items:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(154, 6, lbl)
        pdf.cell(0, 6, "Rs. " + amt, align="R", ln=True)

    pdf.set_draw_color(*BLU)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(255, 220, 220)   # red-tinted total (signals high-risk claim)
    pdf.cell(154, 8, "TOTAL AMOUNT CLAIMED", fill=True)
    pdf.cell(0, 8, "Rs. 8,750/-", align="R", fill=True, ln=True)
    pdf.ln(3)

    # Consultant note
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*ORG)
    pdf.multi_cell(0, 4,
        "Consultant's Note: All procedures in this programme are part of a medically supervised "
        "weight loss plan. Patient is advised to submit this bill to their health insurer for "
        "reimbursement under OPD benefits. Programme is not cosmetic -- it is a therapeutic "
        "intervention for obesity-related metabolic risk reduction.")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(130, 8, "")
    pdf.cell(0, 8, "Dr. Ramesh Nair (Wellness Consultant)", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 6, "Certification: WLC/2021/RN  |  SlimFit Weight Loss & Wellness Centre", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_text_color(*RED)
    pdf.cell(0, 6, "[Clinic Stamp]  -- NOT a government-registered medical practitioner")
    pdf.set_text_color(0, 0, 0)

    out = OUT / "rejected_weight_loss_claim.pdf"
    pdf.output(str(out))
    print(f"Created: {out}")
    print(f"Size: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    gen_rejected_weight_loss()

    # Verify: run through adjudication engine
    print("\n--- Adjudication Preview ---")
    from app.adjudication import adjudicate_claim
    claim = {
        "member_id": "EMP025", "member_name": "Sunita Rao",
        "treatment_date": "2024-10-28", "claim_amount": 8750,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Ramesh Nair",
                "doctor_reg": "WLC/2021/RN",          # INVALID format
                "diagnosis": "Weight loss treatment",  # EXCLUDED
                "procedures": ["Cryolipolysis", "Body wrap therapy", "Liraglutide injection"],
                "medicines_prescribed": ["Liraglutide", "Garcinia Cambogia", "SlimFit Pro"]
            },
            "bill": {
                "consultation_fee": 1500,
                "liraglutide_injection": 2800,
                "body_wrap_therapy": 1200,
                "cryolipolysis_fat_reduction": 2000,
                "dietary_supplements": 500,
                "metabolic_panel": 450,
                "bmi_analysis": 300,
            }
        }
    }
    r = adjudicate_claim(claim, 0, 0)
    print(f"  Decision        : {r['decision']}")
    print(f"  Approved Amount : Rs. {r['approved_amount']}")
    print(f"  Confidence      : {round(r['confidence_score']*100)}%")
    print(f"  Rejection Codes : {', '.join(r['rejection_reasons'])}")
    print(f"  Notes           : {r['notes']}")
