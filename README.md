# ClaimIQ — OPD Claim Adjudication Tool

ClaimIQ is an automated Outpatient Department (OPD) claims adjudication engine. It uses a rules engine coupled with Gemini to instantly process medical documents (bills and prescriptions), apply policy guidelines, and make adjudication decisions.

---

## 💡 What Problem It Solves

Processing health insurance claims manually is slow, expensive, and error-prone. OPD claims (like doctor consultations, pharmacy receipts, and diagnostic lab reports) are high-volume but relatively low-value. Manually verifying every single bill against policy terms, waiting periods, limits, and medical necessity takes weeks.

ClaimIQ automates this entire pipeline, cutting processing time to **under 3 seconds** while checking:
- Policy active status and waiting periods (30-day initial, 90-day specific conditions, 365-day pre-existing).
- Document validity (such as registered doctor license checks via regex, completeness, and date alignment).
- Excluded procedures (e.g. cosmetic teeth whitening) and pre-authorization rules.
- Co-payments, annual/category limits, and network hospital discounts.
- Clinical alignment of diagnosis to tests/medicines.

---

## ⚙️ Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Database / ORM**: SQLite + SQLAlchemy
- **AI Agent**: Google GenAI SDK (Gemini 2.0 Flash / 2.0 Flash Lite / 2.5 Flash)
- **Frontend**: Vanilla HTML5 / Modern CSS (Vanilla) / ES6 JavaScript
- **PDF Generation**: jsPDF + AutoTable (Client-side)

---

## 🏛️ Architecture

The project has a lightweight, modular structure:

```
claimiq/
├── app/
│   ├── static/          # Single-Page App (HTML, CSS, JS)
│   ├── adjudication.py  # 5-step rules engine
│   ├── ai_agent.py      # Gemini Vision & text analysis integration
│   ├── database.py      # SQLAlchemy setup
│   ├── models.py        # SQLite database tables
│   ├── schemas.py       # Pydantic request/response schemas
│   └── main.py          # FastAPI endpoints
├── policy_terms.json    # Policy terms config
├── test_cases.json      # Adjudication test cases
├── requirements.txt     # Python requirements
└── run.py               # Application runner
```

- **Rules Engine**: Operates sequentially through 5 steps (Eligibility, Document Validation, Coverage, Limits, Necessity).
- **Gemini Vision OCR**: Parses uploaded files (images or PDFs), extracts items/diagnoses, and returns structured JSON.
- **Blended Confidence**: Combines the deterministic engine pass/fail score with Gemini's analysis score to determine overall decision reliability.

---

## ✨ Features

- **Gemini Document Parser**: Drag-and-drop a prescription photo or pharmacy bill PDF. It extracts the raw text and populates the claim form instantly.
- **Interactive JSON Viewer**: Expand the raw extraction payload directly in the UI.
- **Cashless & Network hospital perks**: Automatic 20% network discounts and cashless approvals at Apollo, Fortis, Max, Manipal, and Narayana.
- **Partial Approvals**: Auto-detects and deducts excluded procedures (e.g. cosmetic teeth whitening) from the final payout rather than rejecting the whole claim.
- **Live Dashboard**: Real-time tracking of approval rates, successful adjudications, total disbursements, and manual reviews in a sleek dark interface.
- **UI Test Runner**: Execute the 10 core regression test cases directly from the browser and expand their audit trails.
- **Decision PDF Exporter**: Generate and download structured claim receipts including decision status, limits applied, and complete audit trail table.

---

## 🚀 How to Run It

### 1. Set Up Environment
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies
Make sure you have Python 3.10+ installed. Set up your virtual env and install:
```bash
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 3. Run Automated Evals
To verify the adjudication logic against the 10 test cases:
```bash
python run_evals.py
```

### 4. Start the Application
Start the FastAPI server:
```bash
python run.py
```
Open your browser and navigate to:
- **Web App**: http://localhost:8000
- **API Docs (Swagger UI)**: http://localhost:8000/docs
