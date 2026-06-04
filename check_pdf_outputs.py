from app.adjudication import adjudicate_claim

cases = [
    {
        "name": "prescription_fever.pdf",
        "member_id": "EMP001", "member_name": "Rajesh Kumar",
        "treatment_date": "2024-11-01", "claim_amount": 1500,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Rajan Sharma", "doctor_reg": "KA/45678/2015",
                "diagnosis": "Viral fever",
                "medicines_prescribed": ["Paracetamol 650mg", "Vitamin C 500mg", "Cetirizine 10mg"]
            },
            "bill": {"consultation_fee": 1000, "diagnostic_tests": 500}
        }
    },
    {
        "name": "dental_bill.pdf",
        "member_id": "EMP002", "member_name": "Priya Singh",
        "treatment_date": "2024-10-15", "claim_amount": 12000,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Anil Patel", "doctor_reg": "MH/23456/2018",
                "diagnosis": "Tooth decay requiring root canal",
                "procedures": ["Root canal treatment", "Teeth whitening"]
            },
            "bill": {"root_canal": 8000, "teeth_whitening": 4000}
        }
    },
    {
        "name": "lab_diagnostic_report.pdf",
        "member_id": "EMP001", "member_name": "Rajesh Kumar",
        "treatment_date": "2024-11-01", "claim_amount": 500,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Rajan Sharma", "doctor_reg": "KA/45678/2015",
                "diagnosis": "Viral fever",
                "tests_prescribed": ["CBC", "Dengue NS1 Antigen"]
            },
            "bill": {"cbc_test": 350, "dengue_ns1_panel": 150}
        }
    },
    {
        "name": "pharmacy_bill.pdf",
        "member_id": "EMP003", "member_name": "Amit Verma",
        "treatment_date": "2024-10-20", "claim_amount": 1105,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Rajeev Gupta", "doctor_reg": "DL/34567/2016",
                "diagnosis": "Acute Gastroenteritis",
                "medicines_prescribed": ["Norfloxacin+Metronidazole", "Loperamide", "Racecadotril", "ORS Sachets", "Pantoprazole", "Probiotic Sachet"]
            },
            "bill": {"medicines": 1105}
        }
    },
    {
        "name": "hospital_opd_bill.pdf",
        "member_id": "EMP010", "member_name": "Deepak Shah",
        "treatment_date": "2024-11-03", "claim_amount": 4500,
        "hospital": "Apollo Hospitals", "cashless_request": True,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Subramaniam Iyer", "doctor_reg": "TN/56789/2013",
                "diagnosis": "Acute bronchitis",
                "medicines_prescribed": ["Amoxicillin-Clavulanate", "Salbutamol Inhaler", "Budesonide Inhaler", "Doxycycline", "Ambroxol"]
            },
            "bill": {
                "consultation_fee": 1500, "chest_xray": 500,
                "spirometry": 800, "nebulisation": 300, "medicines": 1400
            }
        }
    },
]

SEP = "=" * 68
for c in cases:
    nm = c.pop("name")
    r = adjudicate_claim(c, 0, 0)
    print(SEP)
    print("  FILE:", nm)
    print(SEP)
    print("  Decision        :", r["decision"])
    print("  Approved Amount : Rs.", r["approved_amount"])
    print("  Confidence      :", str(round(r["confidence_score"] * 100)) + "%")
    if r["rejection_reasons"]:
        print("  Rejection Codes :", ", ".join(r["rejection_reasons"]))
    if r["deductions"]:
        for k, v in r["deductions"].items():
            print("  Deduction (" + k + "): Rs.", v)
    if r["partial_items_excluded"]:
        print("  Excluded Items  :", ", ".join(r["partial_items_excluded"]))
    cashless = r.get("cashless_approved", False)
    if cashless:
        print("  Cashless        : YES -- Apollo is a network hospital")
    print("  Notes           :", r["notes"])
    print("  Next Steps      :", r["next_steps"])
    print()
