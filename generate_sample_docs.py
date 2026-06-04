"""
generate_sample_docs.py  --  compatible with fpdf2 >= 2.5
Generates 5 realistic sample medical PDFs for Plum OPD Claim Adjudication Tool.

Files:
  sample_documents/
    1. prescription_fever.pdf         - Doctor prescription (viral fever)
    2. dental_bill.pdf                - Dental clinic bill (root canal + whitening)
    3. lab_diagnostic_report.pdf      - Lab CBC + Dengue report
    4. pharmacy_bill.pdf              - Pharmacy medicines bill
    5. hospital_opd_bill.pdf          - Apollo Hospital OPD bill (network cashless)
"""

from fpdf import FPDF
from pathlib import Path

OUT = Path("sample_documents")
OUT.mkdir(exist_ok=True)

BLU = (30, 58, 138)
LBL = (230, 236, 255)
GRN = (0, 130, 0)
RED = (180, 30, 30)
GRY = (80, 80, 80)


def new_pdf(title, sub):
    """Return a blank A4 PDF with a blue header and footer."""
    class Doc(FPDF):
        def header(self):
            self.set_fill_color(*BLU)
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


def total_row(pdf, label, amount):
    pdf.set_fill_color(*LBL)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(140, 8, label, fill=True)
    pdf.cell(0, 8, "Rs. " + amount, align="R", fill=True, ln=True)


# =============================================================================
# 1. PRESCRIPTION -- Viral Fever
# =============================================================================
def gen_prescription_fever():
    pdf = new_pdf(
        "Dr. Rajan Sharma -- MBBS, MD (General Medicine)",
        "Reg: KA/45678/2015  |  City Clinic, 14 MG Road, Bengaluru-560001  |  Ph: 080-4567-8910"
    )

    sec(pdf, "PATIENT DETAILS")
    kv(pdf, "Patient Name",  "Rajesh Kumar")
    kv(pdf, "Age / Gender",  "34 Years / Male")
    kv(pdf, "Member ID",     "EMP001")
    kv(pdf, "Date of Visit", "01-Nov-2024")
    kv(pdf, "Referred By",   "Self")
    pdf.ln(3)

    sec(pdf, "CLINICAL DIAGNOSIS")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*RED)
    pdf.cell(0, 7, "Viral Fever with mild upper respiratory tract infection (URTI)", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5,
        "Patient presents with high-grade fever (102 F) for 3 days, sore throat, "
        "rhinorrhoea, and body ache. No signs of bacterial infection. "
        "CBC and Dengue serology ordered to rule out secondary infection.")
    pdf.ln(3)

    sec(pdf, "PRESCRIPTION (Rx)")
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 5, "  * Prefer generic equivalents wherever available", ln=True)
    pdf.ln(1)
    thead(pdf, ["#", "Medicine / Drug", "Dosage", "Duration"], [8, 90, 60, 24])
    meds = [
        ("1", "Paracetamol 650 mg",           "1 tab TDS (after food)", "5 days"),
        ("2", "Vitamin C 500 mg",              "1 tab OD",               "7 days"),
        ("3", "Cetirizine 10 mg",              "1 tab HS (at bedtime)",  "5 days"),
        ("4", "ORS Sachets",                   "1 sachet TDS in water",  "3 days"),
        ("5", "Ibuprofen 400 mg (if reqd.)",   "1 tab BD after food",    "3 days"),
    ]
    for i, r in enumerate(meds):
        trow(pdf, r, [8, 90, 60, 24], shade=(i % 2 == 0))
    pdf.ln(4)

    sec(pdf, "INVESTIGATIONS ORDERED")
    thead(pdf, ["Test Name", "Urgency", "Notes"], [90, 35, 57])
    tests = [
        ("Complete Blood Count (CBC)", "Same Day", "Check WBC and platelet levels"),
        ("NS1 Antigen -- Dengue",      "Same Day", "Rule out dengue fever"),
    ]
    for i, r in enumerate(tests):
        trow(pdf, r, [90, 35, 57], shade=(i % 2 == 0))
    pdf.ln(4)

    sec(pdf, "ADVICE")
    pdf.set_font("Helvetica", "", 9)
    for a in [
        "Take complete rest for 3-5 days.",
        "Drink 3-4 litres of fluids daily (water, ORS, coconut water).",
        "Return immediately if fever > 103 F or rash develops.",
        "Follow-up after 5 days or earlier if symptoms worsen.",
    ]:
        pdf.cell(0, 5, "  -  " + a, ln=True)
    pdf.ln(5)

    divider(pdf)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Consultation Fee: Rs. 1,000/-", ln=True)
    pdf.ln(4)
    pdf.cell(130, 8, "")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 8, "Dr. Rajan Sharma", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 6, "MBBS, MD  |  Reg: KA/45678/2015", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_text_color(*GRN)
    pdf.cell(0, 6, "[Signed & Stamped]", ln=True)

    pdf.output(str(OUT / "prescription_fever.pdf"))
    print("  Created: prescription_fever.pdf")


# =============================================================================
# 2. DENTAL BILL -- Root Canal + Whitening
# =============================================================================
def gen_dental_bill():
    pdf = new_pdf(
        "SmilePerfect Dental Clinic",
        "Dr. Anil Patel, BDS MDS (Endodontics)  |  Reg: MH/23456/2018  "
        "|  Shop 7, FC Road, Pune-411004  |  Ph: 020-6789-0123"
    )

    sec(pdf, "PATIENT INFORMATION")
    kv(pdf, "Patient Name",  "Priya Singh")
    kv(pdf, "Age / Gender",  "28 Years / Female")
    kv(pdf, "Member ID",     "EMP002")
    kv(pdf, "Date",          "15-Oct-2024")
    kv(pdf, "Bill No.",      "SMPC-2024-0552")
    pdf.ln(3)

    sec(pdf, "DIAGNOSIS")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*RED)
    pdf.cell(0, 7, "Severe Tooth Decay -- Root Canal Treatment required for Tooth #16", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5,
        "Patient presents with severe toothache radiating to the jaw for 2 weeks. "
        "Dental X-ray reveals deep carious lesion reaching the pulp. "
        "Root Canal Treatment (RCT) performed over 3 sittings. "
        "Patient also opted for cosmetic teeth whitening (elective procedure).")
    pdf.ln(3)

    sec(pdf, "PROCEDURES PERFORMED")
    thead(pdf, ["#", "Procedure", "Area", "Fee (Rs.)"], [8, 105, 42, 27])
    procs = [
        ("1", "Root Canal Treatment -- 3 sittings", "Tooth #16",  "8,000"),
        ("2", "Teeth Whitening (Zoom -- Cosmetic)", "Full Arch",   "4,000"),
    ]
    for i, r in enumerate(procs):
        trow(pdf, r, [8, 105, 42, 27], shade=(i % 2 == 0))
    pdf.ln(4)

    sec(pdf, "MEDICINES PRESCRIBED")
    thead(pdf, ["Medicine", "Dosage", "Duration"], [100, 55, 27])
    meds = [
        ("Amoxicillin 500 mg + Clavulanate",   "1 tab TDS after food", "5 days"),
        ("Ibuprofen + Paracetamol 400/325 mg", "1 tab SOS for pain",   "3 days"),
        ("Chlorhexidine 0.2% Mouthwash",       "Rinse BD",             "7 days"),
    ]
    for i, r in enumerate(meds):
        trow(pdf, r, [100, 55, 27], shade=(i % 2 == 0))
    pdf.ln(4)

    sec(pdf, "BILL SUMMARY")
    for lbl, amt in [("Root Canal Treatment", "8,000"), ("Teeth Whitening (Cosmetic)", "4,000")]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(154, 6, lbl)
        pdf.cell(0, 6, "Rs. " + amt, align="R", ln=True)
    divider(pdf)
    total_row(pdf, "TOTAL AMOUNT DUE", "12,000/-")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 70, 0)
    pdf.multi_cell(0, 4,
        "NOTE: Root Canal Treatment (RCT) is covered under most OPD policies. "
        "Teeth Whitening is a COSMETIC procedure and is typically EXCLUDED from standard OPD cover.")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(130, 8, "")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 8, "Dr. Anil Patel, BDS MDS", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_text_color(*GRN)
    pdf.cell(0, 6, "[Clinic Stamp & Signature]")

    pdf.output(str(OUT / "dental_bill.pdf"))
    print("  Created: dental_bill.pdf")


# =============================================================================
# 3. LAB DIAGNOSTIC REPORT -- CBC + Dengue
# =============================================================================
def gen_lab_report():
    pdf = new_pdf(
        "HealthPath Diagnostics & Pathology Lab -- NABL Accredited",
        "12 Science Park, Koramangala, Bengaluru-560095  |  Ph: 080-1234-5678  |  lab@healthpath.in"
    )

    sec(pdf, "PATIENT & SAMPLE DETAILS")
    kv(pdf, "Patient Name",      "Rajesh Kumar")
    kv(pdf, "Age / Gender",      "34 Years / Male")
    kv(pdf, "Member ID",         "EMP001")
    kv(pdf, "Referred By",       "Dr. Rajan Sharma (Reg: KA/45678/2015)")
    kv(pdf, "Sample Collected",  "01-Nov-2024  10:30 AM")
    kv(pdf, "Report Date",       "01-Nov-2024  05:00 PM")
    kv(pdf, "Sample ID",         "HP-2024-11-0087")
    pdf.ln(3)

    sec(pdf, "COMPLETE BLOOD COUNT (CBC)")
    thead(pdf, ["Parameter", "Result", "Unit", "Ref. Range", "Flag"], [68, 25, 20, 48, 21])
    cbc = [
        ("Haemoglobin (Hb)",         "13.2",    "g/dL",   "13.0-17.0",     "Normal"),
        ("Total Leucocytes (TLC)",   "4,200",   "/cumm",  "4000-11000",    "Normal"),
        ("Neutrophils",              "58",      "%",      "40-75",         "Normal"),
        ("Lymphocytes",              "36",      "%",      "20-40",         "Normal"),
        ("Platelets (PLT)",          "1,05,000","/cumm",  "1.5-4.5 Lac",   "LOW"),
        ("Packed Cell Volume (PCV)", "39",      "%",      "40-54",         "Normal"),
        ("MCV",                      "82",      "fL",     "80-100",        "Normal"),
        ("ESR",                      "22",      "mm/hr",  "0-15",          "HIGH"),
    ]
    for i, r in enumerate(cbc):
        flag = r[4]
        if flag in ("LOW", "HIGH"):
            pdf.set_text_color(*RED)
        trow(pdf, r, [68, 25, 20, 48, 21], shade=(i % 2 == 0))
        pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    sec(pdf, "DENGUE SEROLOGY")
    thead(pdf, ["Test", "Result", "Interpretation"], [90, 30, 62])
    dengue = [
        ("NS1 Antigen (Dengue)",  "NEGATIVE", "No active dengue infection"),
        ("Dengue IgM Antibody",   "NEGATIVE", "No recent dengue infection"),
        ("Dengue IgG Antibody",   "NEGATIVE", "No past dengue infection"),
    ]
    for i, r in enumerate(dengue):
        trow(pdf, r, [90, 30, 62], shade=(i % 2 == 0))
    pdf.ln(4)

    sec(pdf, "INTERPRETATION")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5,
        "CBC findings are consistent with a viral infection. Mild thrombocytopenia (low platelets) "
        "is likely secondary to the viral fever and should be monitored. Dengue serology is NEGATIVE, "
        "ruling out dengue fever. ESR mildly elevated -- correlates with fever. "
        "Recommend repeat CBC after 5 days to ensure platelet recovery.")
    pdf.ln(4)

    sec(pdf, "CHARGES")
    for lbl, amt in [("CBC with Differential Count", "350"), ("Dengue NS1 + IgM/IgG Panel", "150")]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(154, 6, lbl)
        pdf.cell(0, 6, "Rs. " + amt, align="R", ln=True)
    divider(pdf)
    total_row(pdf, "TOTAL CHARGES", "500/-")
    pdf.ln(5)
    pdf.cell(130, 8, "")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 8, "Dr. Preethi Suresh, MD Pathology", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 6, "Lab Director  |  Reg: KA/78901/2016", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_text_color(*GRN)
    pdf.cell(0, 6, "[Lab Seal & Authorised Signatory]")

    pdf.output(str(OUT / "lab_diagnostic_report.pdf"))
    print("  Created: lab_diagnostic_report.pdf")


# =============================================================================
# 4. PHARMACY BILL -- Gastroenteritis medicines
# =============================================================================
def gen_pharmacy_bill():
    pdf = new_pdf(
        "MedPlus Pharmacy  |  GSTIN: 07AABCM1234D1Z5",
        "Shop 3, Connaught Place, New Delhi-110001  |  Ph: 011-2345-6789  |  Lic: DL/21B/2019"
    )

    sec(pdf, "PRESCRIPTION DETAILS")
    kv(pdf, "Patient Name",    "Amit Verma")
    kv(pdf, "Age / Gender",    "41 Years / Male")
    kv(pdf, "Member ID",       "EMP003")
    kv(pdf, "Prescribed By",   "Dr. Rajeev Gupta  (Reg: DL/34567/2016)")
    kv(pdf, "Diagnosis",       "Acute Gastroenteritis")
    kv(pdf, "Date",            "20-Oct-2024")
    kv(pdf, "Bill No.",        "MP-2024-00876")
    pdf.ln(3)

    sec(pdf, "MEDICINES DISPENSED")
    thead(pdf, ["#", "Drug Name & Strength", "Qty", "MRP", "Amount"], [8, 100, 15, 30, 29])
    meds = [
        ("1",  "Norfloxacin 400 mg + Metronidazole 500 mg",   "10 tabs", "Rs.3.80/tab",  "38.00"),
        ("2",  "Loperamide HCl 2 mg",                         "10 tabs", "Rs.2.50/tab",  "25.00"),
        ("3",  "Racecadotril 100 mg (Redotil)",                "10 caps", "Rs.18.50/cap", "185.00"),
        ("4",  "ORS Sachets -- Electral (Orange flavour)",     "10 pcs",  "Rs.12.00/pc",  "120.00"),
        ("5",  "Pantoprazole 40 mg",                           "10 tabs", "Rs.5.20/tab",  "52.00"),
        ("6",  "Domperidone 10 mg",                            "10 tabs", "Rs.2.80/tab",  "28.00"),
        ("7",  "Probiotic Sachet -- Bifilac HP",               "10 pcs",  "Rs.38.00/pc",  "380.00"),
        ("8",  "Zinc Sulphate 20 mg",                          "10 tabs", "Rs.8.20/tab",  "82.00"),
        ("9",  "Drotaverine 80 mg (antispasmodic)",            "10 tabs", "Rs.3.80/tab",  "38.00"),
        ("10", "Amylase+Protease+Lipase Digestive Syrup",      "1 btl",   "Rs.85.00",     "85.00"),
    ]
    for i, r in enumerate(meds):
        trow(pdf, r, [8, 100, 15, 30, 29], shade=(i % 2 == 0))

    pdf.ln(2)
    divider(pdf)
    for lbl, amt in [
        ("Subtotal",               "1,033.00"),
        ("GST @ 12%",              "  123.96"),
        ("Patient Discount (5%)",  "- 51.65"),
    ]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(154, 6, lbl)
        pdf.cell(0, 6, "Rs. " + amt, align="R", ln=True)
    total_row(pdf, "NET AMOUNT PAID", "1,105/-")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5,
        "Payment: Cash  |  Tendered: Rs. 1,200  |  Balance Returned: Rs. 95", ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(150, 0, 0)
    pdf.multi_cell(0, 4,
        "CAUTION: Antibiotics dispensed only against a valid prescription. "
        "Complete the full course as prescribed by your doctor.")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(130, 8, "")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 8, "Authorised Pharmacist", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 6, "Sanjay Malhotra  |  Lic: DL-PH/2019/1234", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_text_color(*GRN)
    pdf.cell(0, 6, "[Pharmacy Stamp & Seal]")

    pdf.output(str(OUT / "pharmacy_bill.pdf"))
    print("  Created: pharmacy_bill.pdf")


# =============================================================================
# 5. HOSPITAL OPD BILL -- Apollo Network Hospital (TC010 cashless style)
# =============================================================================
def gen_hospital_opd_bill():
    pdf = new_pdf(
        "Apollo Hospitals -- Outpatient Department",
        "21 Greams Lane, Chennai-600006  |  Ph: 044-2829-3333  |  ROHINI: 04-01-001-000368-C"
    )

    # Network badge
    pdf.set_fill_color(255, 243, 205)
    pdf.set_text_color(130, 80, 0)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 7,
        "  * NETWORK HOSPITAL -- Plum Benefits OPD Policy (PLUM_OPD_2024)"
        "  |  Cashless & Reimbursement Claims Accepted  *",
        fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    sec(pdf, "PATIENT & VISIT DETAILS")
    kv(pdf, "Patient Name",    "Deepak Shah")
    kv(pdf, "Age / Gender",    "39 Years / Male")
    kv(pdf, "Member ID",       "EMP010")
    kv(pdf, "UHID",            "APL-CHN-20241103-00892")
    kv(pdf, "Date of Visit",   "03-Nov-2024")
    kv(pdf, "Department",      "Internal Medicine / Pulmonology")
    kv(pdf, "Treating Doctor", "Dr. Subramaniam Iyer  |  MBBS, MD (Pulm.)  |  Reg: TN/56789/2013")
    kv(pdf, "Hospital",        "Apollo Hospitals")
    kv(pdf, "TPA / Insurer",   "Plum Benefits  |  Policy: PLUM_OPD_2024")
    pdf.ln(3)

    sec(pdf, "CLINICAL DIAGNOSIS")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*RED)
    pdf.cell(0, 7, "Acute Bronchitis with mild Wheeze -- Infective (Bacterial) Aetiology", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5,
        "Patient presents with 5-day productive cough (yellowish sputum), low-grade fever (99.8 F), "
        "mild dyspnoea on exertion, and audible wheeze on auscultation. "
        "Chest X-ray: peribronchial thickening, no consolidation. "
        "Spirometry: FEV1 78% predicted (mild obstruction). No signs of pneumonia.")
    pdf.ln(3)

    sec(pdf, "SERVICES RENDERED")
    thead(pdf, ["#", "Service / Item", "Qty", "Rate (Rs.)", "Amt (Rs.)"], [6, 105, 12, 28, 31])
    services = [
        ("1",  "OPD Consultation -- Senior Specialist",  "1",   "1,500", "1,500"),
        ("2",  "Chest X-Ray (PA View) -- Digital",       "1",   "500",   "500"),
        ("3",  "Spirometry / Pulmonary Function Test",   "1",   "800",   "800"),
        ("4",  "Nebulisation (Salbutamol 2.5 mg)",       "2",   "150",   "300"),
        ("5",  "Amoxicillin-Clavulanate 625 mg (10 tab)", "1",  "220",   "220"),
        ("6",  "Salbutamol Inhaler 100 mcg (Asthalin)",  "1",   "95",    "95"),
        ("7",  "Budesonide 200 mcg Inhaler (Budecort)",  "1",   "285",   "285"),
        ("8",  "Doxycycline 100 mg caps (10 caps)",      "1",   "110",   "110"),
        ("9",  "Cetirizine 10 mg (10 tabs)",             "1",   "45",    "45"),
        ("10", "Ambroxol 75 mg SR caps (10 caps)",       "1",   "145",   "145"),
    ]
    for i, r in enumerate(services):
        trow(pdf, r, [6, 105, 12, 28, 31], shade=(i % 2 == 0))
    pdf.ln(3)

    sec(pdf, "BILL CALCULATION")
    for lbl, amt in [
        ("Gross Total (OPD Services + Medicines)", "4,500"),
        ("Network Hospital Discount (20%)",        "- 900"),
        ("Patient Co-payment (TPA Policy)",        "0"),
    ]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(154, 6, lbl)
        pdf.cell(0, 6, "Rs. " + amt, align="R", ln=True)
    divider(pdf)

    pdf.set_fill_color(220, 255, 220)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(154, 8, "NET PAYABLE (after network discount)", fill=True)
    pdf.cell(0, 8, "Rs. 3,600/-", align="R", fill=True, ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 5,
        "Cashless Request: APPROVED  |"
        " Insurance Ref: PLUM-2024-CLM-DCSH-110  |"
        " Network Discount: Rs. 900", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(130, 8, "")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 8, "Billing Officer -- Apollo Hospitals", ln=True)
    pdf.cell(130, 6, "")
    pdf.set_text_color(*GRN)
    pdf.cell(0, 6, "[Apollo Hospitals Official Stamp & Seal]")

    pdf.output(str(OUT / "hospital_opd_bill.pdf"))
    print("  Created: hospital_opd_bill.pdf")


# =============================================================================
# Entry point
# =============================================================================
if __name__ == "__main__":
    print("\nGenerating 5 sample medical documents...\n")
    gen_prescription_fever()
    gen_dental_bill()
    gen_lab_report()
    gen_pharmacy_bill()
    gen_hospital_opd_bill()

    print(f"\nAll files saved to: {OUT.resolve()}\n")
    for f in sorted(OUT.glob("*.pdf")):
        print(f"  {f.name:40s}  {f.stat().st_size // 1024} KB")
    print()
