/* =========================================================
   Plum OPD Claim Adjudication — Frontend Application Logic
   ========================================================= */

"use strict";

// ─── State ──────────────────────────────────────────────────
const API = "";   // same origin
let currentPage = "dashboard";

// ─── Test case data (mirrors test_cases.json) ────────────────
const TEST_CASES_DATA = [
  {
    member_id: "EMP001", member_name: "Rajesh Kumar",
    treatment_date: "2024-11-01", claim_amount: 1500,
    documents: {
      prescription: { doctor_name: "Dr. Sharma", doctor_reg: "KA/45678/2015", diagnosis: "Viral fever", medicines_prescribed: ["Paracetamol 650mg", "Vitamin C"] },
      bill: { consultation_fee: 1000, diagnostic_tests: 500 }
    }
  },
  {
    member_id: "EMP002", member_name: "Priya Singh",
    treatment_date: "2024-10-15", claim_amount: 12000,
    documents: {
      prescription: { doctor_name: "Dr. Patel", doctor_reg: "MH/23456/2018", diagnosis: "Tooth decay requiring root canal", procedures: ["Root canal treatment", "Teeth whitening"] },
      bill: { root_canal: 8000, teeth_whitening: 4000 }
    }
  },
  {
    member_id: "EMP003", member_name: "Amit Verma",
    treatment_date: "2024-10-20", claim_amount: 7500,
    documents: {
      prescription: { doctor_name: "Dr. Gupta", doctor_reg: "DL/34567/2016", diagnosis: "Gastroenteritis", medicines_prescribed: ["Antibiotics", "Probiotics"] },
      bill: { consultation_fee: 2000, medicines: 5500 }
    }
  },
  {
    member_id: "EMP004", member_name: "Sneha Reddy",
    treatment_date: "2024-10-25", claim_amount: 2000,
    documents: {
      bill: { consultation_fee: 1500, medicines: 500 }
    }
  },
  {
    member_id: "EMP005", member_name: "Vikram Joshi",
    member_join_date: "2024-09-01", treatment_date: "2024-10-15", claim_amount: 3000,
    documents: {
      prescription: { doctor_name: "Dr. Mehta", doctor_reg: "GJ/56789/2014", diagnosis: "Type 2 Diabetes", medicines_prescribed: ["Metformin", "Glimepiride"] },
      bill: { consultation_fee: 1000, medicines: 2000 }
    }
  },
  {
    member_id: "EMP006", member_name: "Kavita Nair",
    treatment_date: "2024-10-28", claim_amount: 4000,
    documents: {
      prescription: { doctor_name: "Vaidya Krishnan", doctor_reg: "AYUR/KL/2345/2019", diagnosis: "Chronic joint pain", treatment: "Panchakarma therapy" },
      bill: { consultation_fee: 1000, therapy_charges: 3000 }
    }
  },
  {
    member_id: "EMP007", member_name: "Suresh Patil",
    treatment_date: "2024-11-02", claim_amount: 15000,
    documents: {
      prescription: { doctor_name: "Dr. Rao", doctor_reg: "AP/67890/2017", diagnosis: "Suspected lumbar disc herniation", tests_prescribed: ["MRI Lumbar Spine"] },
      bill: { mri_scan: 15000 }
    }
  },
  {
    member_id: "EMP008", member_name: "Ravi Menon",
    treatment_date: "2024-10-30", claim_amount: 4800,
    previous_claims_same_day: 3,
    documents: {
      prescription: { doctor_name: "Dr. Khan", doctor_reg: "UP/45678/2016", diagnosis: "Migraine", medicines_prescribed: ["Sumatriptan", "Propranolol"] },
      bill: { consultation_fee: 2000, medicines: 2800 }
    }
  },
  {
    member_id: "EMP009", member_name: "Anita Desai",
    treatment_date: "2024-10-18", claim_amount: 8000,
    documents: {
      prescription: { doctor_name: "Dr. Banerjee", doctor_reg: "WB/34567/2015", diagnosis: "Obesity - BMI 35", treatment: "Bariatric consultation and diet plan" },
      bill: { consultation_fee: 3000, diet_plan: 5000 }
    }
  },
  {
    member_id: "EMP010", member_name: "Deepak Shah",
    treatment_date: "2024-11-03", claim_amount: 4500,
    hospital: "Apollo Hospitals", cashless_request: true,
    documents: {
      prescription: { doctor_name: "Dr. Iyer", doctor_reg: "TN/56789/2013", diagnosis: "Acute bronchitis", medicines_prescribed: ["Antibiotics", "Bronchodilators"] },
      bill: { consultation_fee: 1500, medicines: 3000 }
    }
  },
];

// ─── Navigation ──────────────────────────────────────────────

function showPage(page) {
  document.querySelectorAll("section[id^='page-']").forEach(s => s.style.display = "none");
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const section = document.getElementById(`page-${page}`);
  if (section) section.style.display = "block";

  const navEl = document.getElementById(`nav-${page}`);
  if (navEl) navEl.classList.add("active");

  currentPage = page;

  if (page === "dashboard") loadDashboard();
  if (page === "claims")    loadClaimsList();
  if (page === "policy")    loadPolicy();
}

// ─── Dashboard ───────────────────────────────────────────────

async function loadDashboard() {
  try {
    const [stats, claims] = await Promise.all([
      apiFetch("/api/stats"),
      apiFetch("/api/claims"),
    ]);

    document.getElementById("stat-total").textContent    = stats.total_claims;
    document.getElementById("stat-rate").textContent     = `${stats.approval_rate}%`;
    document.getElementById("stat-approved-count").textContent = `${stats.approved} approved`;
    document.getElementById("stat-rejected").textContent = stats.rejected;
    document.getElementById("stat-manual").textContent   = stats.manual_review;
    document.getElementById("stat-disbursed").textContent = `₹${formatNum(stats.total_approved_amount)}`;
    document.getElementById("stat-confidence").textContent = `AI confidence ${stats.avg_confidence}%`;
    // New cards
    const succEl = document.getElementById("stat-successful");
    if (succEl) succEl.textContent = stats.successful_adjudications ?? (stats.approved + stats.partial);
    const rateEl = document.getElementById("stat-success-rate");
    if (rateEl) rateEl.textContent = `${stats.success_rate ?? 0}% success rate`;

    const wrap = document.getElementById("recentClaimsWrap");
    if (!claims.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No claims yet.</p></div>`;
      return;
    }
    wrap.innerHTML = renderClaimsTable(claims, true);
  } catch (e) {
    console.error(e);
  }
}

// ─── Claims List ─────────────────────────────────────────────

async function loadClaimsList() {
  const wrap = document.getElementById("claimsTableWrap");
  try {
    const claims = await apiFetch("/api/claims");
    if (!claims.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No claims submitted yet.</p></div>`;
      return;
    }
    wrap.innerHTML = renderClaimsTable(claims, false);
  } catch (e) {
    wrap.innerHTML = `<div class="empty-state"><p>Failed to load claims.</p></div>`;
  }
}

function renderClaimsTable(claims, compact) {
  const rows = claims.map(c => `
    <tr onclick="openClaim('${c.claim_id}')">
      <td><span style="font-family:'Outfit',sans-serif;font-weight:600">${c.claim_id}</span></td>
      <td>${c.member_name}</td>
      <td>${c.treatment_date}</td>
      <td>₹${formatNum(c.claim_amount)}</td>
      <td><span class="status-badge status-${c.decision}">${decisionIcon(c.decision)} ${c.decision}</span></td>
      <td>${approvedAmountCell(c.decision, c.approved_amount)}</td>
      ${!compact ? `<td>${confidencePill(c.confidence_score)}</td>` : ""}
      <td style="color:var(--text-muted);font-size:12px">${formatDate(c.submitted_at)}</td>
    </tr>`).join("");

  return `
    <table class="claims-table">
      <thead>
        <tr>
          <th>Claim ID</th><th>Member</th><th>Date</th><th>Amount</th>
          <th>Decision</th><th>Approved</th>${!compact ? "<th>Confidence</th>" : ""}
          <th>Submitted</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

async function openClaim(claimId) {
  showPage("claim-detail");
  document.getElementById("nav-claims").classList.add("active");

  const wrap = document.getElementById("claimDetailContent");
  wrap.innerHTML = `<div class="empty-state"><div class="spinner"></div></div>`;

  try {
    const c = await apiFetch(`/api/claims/${claimId}`);
    wrap.innerHTML = renderClaimDetail(c);
    // Animate confidence ring
    setTimeout(() => animateConfidence(c.confidence_score), 100);
  } catch (e) {
    wrap.innerHTML = `<div class="empty-state"><p>Could not load claim details.</p></div>`;
  }
}

function renderClaimDetail(c) {
  const r = c;
  const pct = Math.round((r.confidence_score || 0) * 100);
  const confLevel = pct >= 85 ? "high" : pct >= 70 ? "medium" : "low";
  const confColor = pct >= 85 ? "var(--success)" : pct >= 70 ? "var(--warning)" : "var(--error)";

  const auditHTML = (r.audit_trail || []).map(step => `
    <div class="audit-step ${step.passed ? "passed" : "failed"}" onclick="toggleAuditStep(this)">
      <div class="audit-step-icon">${step.passed ? "✅" : "❌"}</div>
      <div class="audit-step-body">
        <div class="audit-step-header">
          <div class="audit-step-name">Step ${step.step}: ${step.name}</div>
          <span class="audit-step-badge ${step.passed ? "badge-pass" : "badge-fail"}">${step.passed ? "PASS" : "FAIL"}</span>
        </div>
        <div class="audit-step-detail">${(step.details || []).join(" · ")}</div>
        <div class="audit-step-extra">
          ${(step.rejection_codes || []).length ? `<div style="margin-bottom:8px">${step.rejection_codes.map(c => `<span class="code-pill">${c}</span>`).join("")}</div>` : ""}
          ${renderMiniPolicyTable(step.policy_rules || [])}
        </div>
      </div>
    </div>`).join("");

  const policyRulesHTML = renderPolicyTable(r.policy_rules_applied || []);

  const fraudHTML = (r.fraud_flags || []).length
    ? `<div class="card mb-28" style="border-color:rgba(245,158,11,0.4)">
        <div class="card-title" style="color:var(--warning)">⚠️ Fraud Indicators</div>
        ${r.fraud_flags.map(f => `<div style="font-size:13px; color:var(--warning); margin-bottom:6px">• ${f}</div>`).join("")}
       </div>`
    : "";

  const deductHTML = Object.keys(r.deductions || {}).length
    ? Object.entries(r.deductions).map(([k, v]) =>
        `<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px">
          <span style="color:var(--text-secondary)">${formatKey(k)}</span>
          <span style="color:var(--error)">− ₹${formatNum(v)}</span>
        </div>`).join("")
    : `<div style="color:var(--text-muted);font-size:13px">No deductions applied.</div>`;

  return `
    <!-- Decision Banner -->
    <div class="decision-banner ${r.decision}">
      <div class="decision-left">
        <div class="decision-icon">${decisionBigIcon(r.decision)}</div>
        <div>
          <div class="decision-label">Adjudication Decision</div>
          <div class="decision-text">${r.decision.replace("_", " ")}</div>
          ${r.cashless_approved ? '<div style="margin-top:6px"><span class="status-badge status-APPROVED" style="font-size:11px">💳 Cashless Approved</span></div>' : ""}
        </div>
      </div>
      <div class="decision-right">
        ${r.decision === 'REJECTED'
          ? `<div class="decision-amount" style="color:var(--error)">₹0</div>
             <div class="decision-amount-label">Approved Amount</div>`
          : r.decision === 'MANUAL_REVIEW'
          ? `<div class="decision-amount" style="color:var(--warning);font-size:1.6rem">Pending</div>
             <div class="decision-amount-label">Final amount not yet determined</div>`
          : `<div class="decision-amount">₹${formatNum(r.approved_amount || 0)}</div>
             <div class="decision-amount-label">Approved Amount</div>`
        }
        <div style="margin-top:6px;font-size:12px;color:var(--text-secondary)">Claimed: ₹${formatNum(r.claim_amount)}</div>
        <button onclick="downloadDecisionReport()" style="margin-top:10px;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#fff;border-radius:8px;padding:6px 14px;font-size:11px;cursor:pointer;display:flex;align-items:center;gap:6px" title="Download PDF report">
          📥 Download Decision Report
        </button>
      </div>
    </div>

    <!-- Top info strip -->
    <div class="grid-3 mb-28">
      <!-- Confidence -->
      <div class="card confidence-card">
        <div class="confidence-ring-wrap">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle class="confidence-ring-bg" cx="40" cy="40" r="34"/>
            <circle class="confidence-ring-fill ${confLevel}" id="confRing"
              cx="40" cy="40" r="34"
              stroke-dashoffset="220"
              data-pct="${pct}"/>
          </svg>
          <div class="confidence-pct" style="color:${confColor}">${pct}%</div>
        </div>
        <div class="confidence-info">
          <div class="confidence-label">AI Confidence</div>
          <div class="confidence-val" style="color:${confColor}">${pct >= 85 ? "HIGH" : pct >= 70 ? "MEDIUM" : "LOW"}</div>
          <div class="confidence-desc">${pct >= 85 ? "Decision is highly reliable" : pct >= 70 ? "Decision is reasonably reliable" : "Manual review recommended"}</div>
        </div>
      </div>

      <!-- Member Info -->
      <div class="card">
        <div class="card-title">Member Details</div>
        <div style="font-size:13px;line-height:1.9;color:var(--text-secondary)">
          <div><strong style="color:var(--text-primary)">${r.member_name}</strong></div>
          <div>ID: ${r.member_id}</div>
          <div>Treatment: ${r.treatment_date}</div>
          ${r.hospital ? `<div>Hospital: ${r.hospital}</div>` : ""}
        </div>
      </div>

      <!-- Deductions -->
      <div class="card">
        <div class="card-title">Deductions</div>
        ${deductHTML}
        ${Object.keys(r.deductions || {}).length ? `<div style="display:flex;justify-content:space-between;padding-top:10px;font-size:13px;font-weight:600"><span>Approved Total</span><span style="color:var(--success)">₹${formatNum(r.approved_amount)}</span></div>` : ""}
      </div>
    </div>

    ${fraudHTML}

    <!-- Rejection Reasons -->
    ${(r.rejection_reasons || []).length ? `
    <div class="card mb-28" style="border-color:rgba(239,68,68,0.3)">
      <div class="card-title" style="color:var(--error)">Rejection Reasons</div>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        ${r.rejection_reasons.map(code => `
          <div style="background:var(--error-bg);border:1px solid rgba(239,68,68,0.3);border-radius:10px;padding:10px 16px">
            <div style="font-family:'Outfit',sans-serif;font-weight:700;color:var(--error)">${code}</div>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:2px">${rejectionDesc(code)}</div>
          </div>`).join("")}
      </div>
    </div>` : ""}

    <!-- Partial Exclusions -->
    ${(r.partial_items_excluded || []).length ? `
    <div class="card mb-28" style="border-color:rgba(249,115,22,0.3)">
      <div class="card-title" style="color:var(--partial)">Excluded Items (Partial Approval)</div>
      ${r.partial_items_excluded.map(item => `<div style="font-size:13px;color:var(--text-secondary);margin-bottom:4px">• ${item}</div>`).join("")}
    </div>` : ""}

    <!-- Audit Trail -->
    <div class="card mb-28">
      <div class="card-title">Decision Audit Trail</div>
      <p style="font-size:13px;color:var(--text-secondary);margin-bottom:16px">Click each step to expand details and view the policy rules applied.</p>
      <div class="audit-trail">${auditHTML}</div>
    </div>

    <!-- Policy Explanation Panel -->
    <div class="card mb-28">
      <div class="card-title">Policy Explanation Panel</div>
      <p style="font-size:13px;color:var(--text-secondary);margin-bottom:16px">Every policy rule evaluated during adjudication, with the exact values compared.</p>
      ${policyRulesHTML}
    </div>

    <!-- Next Steps -->
    <div class="card mb-28" style="background:var(--purple-dim);border-color:rgba(124,58,237,0.3)">
      <div class="card-title" style="color:var(--purple-light)">📌 Next Steps</div>
      <div style="font-size:14px;color:var(--text-primary)">${r.next_steps}</div>
      ${r.notes ? `<div style="margin-top:8px;font-size:12px;color:var(--text-secondary)">${r.notes}</div>` : ""}
    </div>

    <!-- Download button (bottom) -->
    <div style="display:flex;gap:12px;justify-content:flex-end">
      <button onclick="downloadDecisionReport()" class="btn btn-primary" style="font-size:13px">
        📥 Download Decision Report (PDF)
      </button>
    </div>`;
}

function renderPolicyTable(rules) {
  if (!rules.length) return `<div class="empty-state" style="padding:20px"><p>No policy rules recorded.</p></div>`;
  const rows = rules.map(r => `
    <tr>
      <td style="color:var(--text-primary);font-weight:500">${r.rule}</td>
      <td style="color:var(--text-secondary)">${r.policy_value}</td>
      <td style="color:var(--text-primary)">${r.claim_value}</td>
      <td><span class="result-chip chip-${r.result}">${r.result}</span></td>
      ${r.note ? `<td style="color:var(--text-muted);font-size:12px">${r.note}</td>` : "<td>—</td>"}
    </tr>`).join("");
  return `
    <table class="policy-table">
      <thead><tr><th>Rule</th><th>Policy Value</th><th>Claim Value</th><th>Result</th><th>Note</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function renderMiniPolicyTable(rules) {
  if (!rules.length) return "";
  const rows = rules.map(r => `
    <tr>
      <td style="font-size:12px;color:var(--text-secondary);padding:4px 8px">${r.rule}</td>
      <td style="font-size:12px;color:var(--text-primary);padding:4px 8px">${r.policy_value} → ${r.claim_value}</td>
      <td style="padding:4px 8px"><span class="result-chip chip-${r.result}" style="font-size:9px">${r.result}</span></td>
    </tr>`).join("");
  return `<table style="width:100%;border-collapse:collapse"><tbody>${rows}</tbody></table>`;
}

function toggleAuditStep(el) {
  el.classList.toggle("open");
}

function animateConfidence(score) {
  const ring = document.getElementById("confRing");
  if (!ring) return;
  const pct = Math.round((score || 0) * 100);
  const circumference = 2 * Math.PI * 34;
  const offset = circumference - (pct / 100) * circumference;
  ring.style.strokeDasharray = circumference;
  ring.style.strokeDashoffset = offset;
}

// ─── New Claim Form ──────────────────────────────────────────

function addBillRow() {
  const container = document.getElementById("billItemsContainer");
  const row = document.createElement("div");
  row.className = "bill-item-row";
  row.style.cssText = "display:grid;grid-template-columns:1fr 1fr auto;gap:12px;margin-bottom:10px;align-items:center";
  row.innerHTML = `
    <input type="text" class="bill-item-key" placeholder="Item (e.g. medicines)" />
    <input type="number" class="bill-item-val" placeholder="Amount (₹)" step="0.01" />
    <button type="button" class="btn btn-secondary btn-sm" onclick="removeBillRow(this)" style="width:36px;height:36px;padding:0;display:flex;align-items:center;justify-content:center">✕</button>`;
  container.appendChild(row);
}

function removeBillRow(btn) {
  const rows = document.querySelectorAll(".bill-item-row");
  if (rows.length > 1) btn.closest(".bill-item-row").remove();
}

function collectBill() {
  const bill = {};
  document.querySelectorAll(".bill-item-row").forEach(row => {
    const key = row.querySelector(".bill-item-key").value.trim().replace(/\s+/g, "_");
    const val = parseFloat(row.querySelector(".bill-item-val").value) || 0;
    if (key) bill[key] = val;
  });
  return bill;
}

function loadTestCase() {
  const idx = parseInt(document.getElementById("testCaseSelect").value);
  if (isNaN(idx)) return showToast("Please select a test case first.", "info");
  const tc = TEST_CASES_DATA[idx];
  if (!tc) return;

  document.getElementById("memberId").value       = tc.member_id || "";
  document.getElementById("memberName").value     = tc.member_name || "";
  document.getElementById("treatmentDate").value  = tc.treatment_date || "";
  document.getElementById("memberJoinDate").value = tc.member_join_date || "";
  document.getElementById("claimAmount").value    = tc.claim_amount || "";
  document.getElementById("hospital").value       = tc.hospital || "";
  document.getElementById("cashlessRequest").checked = !!tc.cashless_request;
  document.getElementById("previousClaims").value = tc.previous_claims_same_day || 0;

  const rx = tc.documents?.prescription || {};
  document.getElementById("doctorName").value    = rx.doctor_name || "";
  document.getElementById("doctorReg").value     = rx.doctor_reg || "";
  document.getElementById("diagnosis").value     = rx.diagnosis || "";
  document.getElementById("treatment").value     = rx.treatment || "";
  document.getElementById("medicines").value     = (rx.medicines_prescribed || []).join(", ");
  document.getElementById("procedures").value    = (rx.procedures || []).join(", ");
  document.getElementById("testsPrescribed").value = (rx.tests_prescribed || []).join(", ");

  // Rebuild bill rows
  const container = document.getElementById("billItemsContainer");
  container.innerHTML = "";
  const bill = tc.documents?.bill || {};
  Object.entries(bill).forEach(([k, v]) => {
    const row = document.createElement("div");
    row.className = "bill-item-row";
    row.style.cssText = "display:grid;grid-template-columns:1fr 1fr auto;gap:12px;margin-bottom:10px;align-items:center";
    row.innerHTML = `
      <input type="text" class="bill-item-key" value="${k}" placeholder="Item" />
      <input type="number" class="bill-item-val" value="${v}" placeholder="Amount (₹)" min="0" step="0.01" />
      <button type="button" class="btn btn-secondary btn-sm" onclick="removeBillRow(this)" style="width:36px;height:36px;padding:0;display:flex;align-items:center;justify-content:center">✕</button>`;
    container.appendChild(row);
  });

  showToast(`Loaded TC${String(idx + 1).padStart(3, "0")} — ${tc.member_name}`, "success");
}

async function submitClaim(e) {
  e.preventDefault();
  const btn  = document.getElementById("submitBtn");
  const text = document.getElementById("submitBtnText");
  btn.disabled = true;
  text.innerHTML = `<span class="spinner"></span> Processing…`;

  const medicines   = document.getElementById("medicines").value.split(",").map(s => s.trim()).filter(Boolean);
  const procedures  = document.getElementById("procedures").value.split(",").map(s => s.trim()).filter(Boolean);
  const testsPrx    = document.getElementById("testsPrescribed").value.split(",").map(s => s.trim()).filter(Boolean);
  const doctorName  = document.getElementById("doctorName").value.trim();
  const doctorReg   = document.getElementById("doctorReg").value.trim();
  const diagnosis   = document.getElementById("diagnosis").value.trim();
  const treatment   = document.getElementById("treatment").value.trim();
  const bill        = collectBill();

  const prescription = {};
  if (doctorName) prescription.doctor_name = doctorName;
  if (doctorReg)  prescription.doctor_reg  = doctorReg;
  if (diagnosis)  prescription.diagnosis   = diagnosis;
  if (treatment)  prescription.treatment   = treatment;
  if (medicines.length)  prescription.medicines_prescribed = medicines;
  if (procedures.length) prescription.procedures = procedures;
  if (testsPrx.length)   prescription.tests_prescribed = testsPrx;

  const payload = {
    member_id:                document.getElementById("memberId").value.trim(),
    member_name:              document.getElementById("memberName").value.trim(),
    treatment_date:           document.getElementById("treatmentDate").value,
    claim_amount:             parseFloat(document.getElementById("claimAmount").value),
    hospital:                 document.getElementById("hospital").value.trim() || null,
    cashless_request:         document.getElementById("cashlessRequest").checked,
    member_join_date:         document.getElementById("memberJoinDate").value || null,
    previous_claims_same_day: parseInt(document.getElementById("previousClaims").value) || 0,
    documents: {
      ...(Object.keys(prescription).length ? { prescription } : {}),
      ...(Object.keys(bill).length ? { bill } : {}),
    },
  };

  try {
    const data = await apiFetch("/api/claims", { method: "POST", body: JSON.stringify(payload) });
    showToast(`Claim ${data.claim_id} — ${data.result.decision}`, data.result.decision === "APPROVED" ? "success" : "info");
    await openClaim(data.claim_id);
  } catch (err) {
    showToast("Failed to submit claim: " + err.message, "error");
  } finally {
    btn.disabled = false;
    text.innerHTML = "⚡ Adjudicate Claim";
  }
}

// ─── Test Runner ─────────────────────────────────────────────

async function runAllTests() {
  const btn  = document.getElementById("runTestsBtn");
  const text = document.getElementById("runTestsBtnText");
  btn.disabled = true;
  text.innerHTML = `<span class="spinner"></span> Running…`;
  document.getElementById("testResultsList").innerHTML = "";
  document.getElementById("testSummaryStrip").style.display = "none";

  try {
    const data = await apiFetch("/api/test-runner/run-all", { method: "POST" });

    // Summary strip
    document.getElementById("ts-total").textContent = data.total;
    document.getElementById("ts-pass").textContent  = data.passed;
    document.getElementById("ts-fail").textContent  = data.failed;
    document.getElementById("ts-rate").textContent  = `${data.pass_rate}%`;
    document.getElementById("ts-progress").style.width = `${data.pass_rate}%`;
    document.getElementById("testSummaryStrip").style.display = "flex";

    // Result cards
    const list = document.getElementById("testResultsList");
    data.results.forEach((r, i) => {
      const card = document.createElement("div");
      card.style.marginBottom = "0";

      const auditSteps = (r.audit_trail || []).map(s =>
        `<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px">
          <span>${s.passed ? "✅" : "❌"}</span>
          <span style="color:var(--text-secondary)">${s.name}</span>
          <span class="audit-step-badge ${s.passed ? "badge-pass" : "badge-fail"}" style="font-size:9px">${s.passed ? "PASS" : "FAIL"}</span>
        </div>`).join("");

      card.innerHTML = `
        <div class="test-result-card ${r.passed ? "passed" : "failed"}" onclick="toggleTestDetail('detail-${i}')">
          <span class="tc-badge">${r.case_id}</span>
          <div style="flex:1">
            <div class="tc-name">${r.case_name}</div>
            <div class="tc-desc">${r.description}</div>
          </div>
          <div class="tc-result-row">
            <span style="font-size:12px;color:var(--text-muted)">Expected</span>
            <span class="status-badge status-${r.expected_decision}" style="font-size:10px">${r.expected_decision}</span>
            <span class="tc-arrow">→</span>
            <span class="status-badge status-${r.actual_decision}" style="font-size:10px">${r.actual_decision}</span>
            <span style="font-size:12px;color:var(--text-muted)">Got</span>
          </div>
          ${r.expected_amount != null
            ? `<div style="font-size:12px;color:var(--text-muted);text-align:right">
                ₹${r.expected_amount} → ₹${r.actual_amount}
                <span style="color:${r.amount_match ? "var(--success)" : "var(--error)"}">${r.amount_match ? "✓" : "✗"}</span>
               </div>`
            : ""}
          <span style="font-size:18px">${r.passed ? "✅" : "❌"}</span>
        </div>
        <div class="test-detail-panel" id="detail-${i}">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:12px">
            <div>
              <div style="color:var(--text-muted);margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:.06em">Audit Trail</div>
              ${auditSteps}
            </div>
            <div>
              <div style="color:var(--text-muted);margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:.06em">Details</div>
              <div style="color:var(--text-secondary)">Confidence: <strong style="color:var(--text-primary)">${Math.round((r.confidence_score || 0) * 100)}%</strong></div>
              ${r.rejection_reasons.length ? `<div style="margin-top:6px">${r.rejection_reasons.map(c => `<span class="code-pill">${c}</span>`).join("")}</div>` : ""}
            </div>
          </div>
        </div>`;
      list.appendChild(card);
    });

    showToast(`${data.passed}/${data.total} tests passed (${data.pass_rate}%)`, data.failed === 0 ? "success" : "info");
  } catch (err) {
    showToast("Test run failed: " + err.message, "error");
  } finally {
    btn.disabled = false;
    text.innerHTML = "▶ Run All Tests";
  }
}

function toggleTestDetail(id) {
  const panel = document.getElementById(id);
  if (panel) panel.classList.toggle("open");
}

// ─── Policy View ─────────────────────────────────────────────

async function loadPolicy() {
  const wrap = document.getElementById("policyContent");
  try {
    const p = await apiFetch("/api/policy");
    const cov = p.coverage_details;
    const wp  = p.waiting_periods;

    const coverageItems = [
      ["Annual Limit",       `₹${formatNum(cov.annual_limit)}`],
      ["Per-Claim Limit",    `₹${formatNum(cov.per_claim_limit)}`],
      ["Family Floater",     `₹${formatNum(cov.family_floater_limit)}`],
      ["Consultation Limit", `₹${formatNum(cov.consultation_fees.sub_limit)}`],
      ["Consultation Co-pay",`${cov.consultation_fees.copay_percentage}%`],
      ["Network Discount",   `${cov.consultation_fees.network_discount}%`],
      ["Pharmacy Limit",     `₹${formatNum(cov.pharmacy.sub_limit)}`],
      ["Dental Limit",       `₹${formatNum(cov.dental.sub_limit)}`],
      ["Vision Limit",       `₹${formatNum(cov.vision.sub_limit)}`],
      ["Alt. Medicine Limit",`₹${formatNum(cov.alternative_medicine.sub_limit)}`],
      ["Diagnostic Tests",   `₹${formatNum(cov.diagnostic_tests.sub_limit)}`],
    ];

    const networkHTML = p.network_hospitals.map(h => `<span class="network-tag">🏥 ${h}</span>`).join("");
    const exclusionHTML = p.exclusions.map(e => `<span class="exclusion-tag">✕ ${e}</span>`).join("");
    const coverageHTML = coverageItems.map(([l, v]) => `
      <div class="policy-item">
        <div class="pi-label">${l}</div>
        <div class="pi-val">${v}</div>
      </div>`).join("");

    wrap.innerHTML = `
      <div class="policy-section">
        <h3>💰 Coverage Limits</h3>
        <div class="policy-grid">${coverageHTML}</div>
      </div>

      <div class="policy-section">
        <h3>⏳ Waiting Periods</h3>
        <div class="policy-grid">
          <div class="policy-item"><div class="pi-label">Initial</div><div class="pi-val">${wp.initial_waiting} days</div></div>
          <div class="policy-item"><div class="pi-label">Pre-existing Diseases</div><div class="pi-val">${wp.pre_existing_diseases} days</div></div>
          <div class="policy-item"><div class="pi-label">Maternity</div><div class="pi-val">${wp.maternity} days</div></div>
          <div class="policy-item"><div class="pi-label">Diabetes / Hypertension</div><div class="pi-val">${wp.specific_ailments.diabetes} days</div></div>
          <div class="policy-item"><div class="pi-label">Joint Replacement</div><div class="pi-val">${wp.specific_ailments.joint_replacement} days</div></div>
        </div>
      </div>

      <div class="policy-section">
        <h3>🏥 Network Hospitals</h3>
        <div>${networkHTML}</div>
      </div>

      <div class="policy-section">
        <h3>🚫 Exclusions</h3>
        <div>${exclusionHTML}</div>
      </div>

      <div class="policy-section">
        <h3>📋 Claim Requirements</h3>
        <div class="policy-grid">
          <div class="policy-item"><div class="pi-label">Minimum Claim</div><div class="pi-val">₹${p.claim_requirements.minimum_claim_amount}</div></div>
          <div class="policy-item"><div class="pi-label">Submission Deadline</div><div class="pi-val">${p.claim_requirements.submission_timeline_days} days</div></div>
          <div class="policy-item"><div class="pi-label">Cashless Available</div><div class="pi-val">${p.cashless_facilities.available ? "Yes" : "No"}</div></div>
        </div>
        <div style="margin-top:12px">
          ${p.claim_requirements.documents_required.map(d => `<div style="font-size:13px;color:var(--text-secondary);padding:4px 0;border-bottom:1px solid var(--border)">• ${d}</div>`).join("")}
        </div>
      </div>`;
  } catch (e) {
    wrap.innerHTML = `<div class="empty-state"><p>Failed to load policy data.</p></div>`;
  }
}

// ─── Document Upload & Gemini Vision Extraction ──────────

let _currentDocFile = null;
let _lastExtraction = null;

function handleDocDrop(e) {
  e.preventDefault();
  document.getElementById("dropZone").classList.remove("dz-active");
  const file = e.dataTransfer.files[0];
  if (file) handleDocFileSelect(file);
}

function handleDocFileSelect(file) {
  if (!file) return;

  const allowed = ["image/jpeg", "image/jpg", "image/png", "image/webp", "application/pdf"];
  if (!allowed.includes(file.type)) {
    showToast("Unsupported file type. Please upload JPG, PNG, WebP or PDF.", "error");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast("File too large (max 10 MB).", "error");
    return;
  }

  _currentDocFile = file;
  _lastExtraction = null;

  // Show preview row
  const previewRow = document.getElementById("docPreviewRow");
  previewRow.style.display = "flex";
  document.getElementById("docFileName").textContent = file.name;
  document.getElementById("docFileSize").textContent =
    `${(file.size / 1024).toFixed(1)} KB · ${file.type}`;

  const thumb = document.getElementById("docPreviewThumb");
  if (file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = ev => {
      thumb.innerHTML = `<img src="${ev.target.result}" style="width:100%;height:100%;object-fit:cover" />`;
    };
    reader.readAsDataURL(file);
  } else {
    thumb.textContent = "📄";
  }

  // Show extract row and hide old result
  document.getElementById("docExtractRow").style.display = "flex";
  const rp = document.getElementById("extractResultPanel");
  rp.style.display = "none";
  rp.innerHTML = "";
}

function clearDocUpload() {
  _currentDocFile = null;
  _lastExtraction = null;
  document.getElementById("docFileInput").value = "";
  document.getElementById("docPreviewRow").style.display = "none";
  document.getElementById("docExtractRow").style.display = "none";
  const rp = document.getElementById("extractResultPanel");
  rp.style.display = "none";
  rp.innerHTML = "";
  document.getElementById("docPreviewThumb").innerHTML = "";
  document.getElementById("docFileName").textContent = "";
}

async function extractDocumentData() {
  if (!_currentDocFile) {
    showToast("No file selected.", "error");
    return;
  }

  const btn  = document.getElementById("extractBtn");
  const text = document.getElementById("extractBtnText");
  btn.disabled = true;
  text.innerHTML = `<span class="spinner"></span> Extracting…`;

  const resultPanel = document.getElementById("extractResultPanel");
  resultPanel.style.display = "block";
  resultPanel.innerHTML = `
    <div style="display:flex;align-items:center;gap:12px;padding:16px;background:var(--surface-2);border:1px solid var(--border);border-radius:var(--radius)">
      <span class="spinner"></span>
      <span style="font-size:13px;color:var(--text-secondary)">Gemini Vision is reading your document…</span>
    </div>`;

  try {
    const docType = document.getElementById("docTypeSelect").value;
    const formData = new FormData();
    formData.append("file", _currentDocFile);
    formData.append("doc_type", docType);

    const res = await fetch("/api/extract-document", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Extraction failed");
    }

    // ── CRITICAL: backend returns HTTP 200 even on AI failure ──
    if (data.success === false) {
      throw new Error(data.error || "Gemini could not read the document. Try a clearer image.");
    }

    // Verify we actually got some data back
    const extracted = data.extracted_data || {};
    const hasData = Object.values(extracted).some(v =>
      v !== null && v !== undefined && v !== "" &&
      !(Array.isArray(v) && v.length === 0) &&
      !(typeof v === "object" && !Array.isArray(v) && Object.keys(v).length === 0)
    );
    if (!hasData) {
      throw new Error("Gemini could not extract any fields from this document. Try a higher quality scan or different file.");
    }

    _lastExtraction = data;
    renderExtractionResult(data, resultPanel);
    showToast("Document extracted — click ⬇ Auto-fill to populate the form.", "success");

  } catch (err) {
    _lastExtraction = null;  // clear stale data
    resultPanel.innerHTML = `
      <div class="extract-error-panel">
        <div style="font-weight:600;color:var(--error);margin-bottom:6px">❌ Extraction Failed</div>
        <div style="font-size:13px;color:var(--text-secondary)">${err.message}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:8px">Tips: ensure the document is clear, not blurry, and text is readable. Max 10 MB.</div>
      </div>`;
    showToast("Extraction failed: " + err.message, "error");
  } finally {
    btn.disabled = false;
    text.innerHTML = "✨ Extract with Gemini";
  }
}

function renderExtractionResult(data, panel) {
  const d = data.extracted_data || {};
  const confPct = Math.round((data.confidence || 0) * 100);
  const confColor = confPct >= 80 ? "var(--success)" : confPct >= 60 ? "var(--warning)" : "var(--error)";

  // Build field display list
  const fields = [
    ["Patient Name",        d.patient_name],
    ["Treatment Date",      d.treatment_date],
    ["Doctor Name",         d.doctor_name],
    ["Doctor Reg. No.",     d.doctor_registration],
    ["Hospital / Clinic",   d.hospital_name],
    ["Diagnosis",           d.diagnosis],
    ["Treatment",           d.treatment],
    ["Medicines",           (d.medicines_prescribed || []).join(", ")],
    ["Tests Prescribed",    (d.tests_prescribed || []).join(", ")],
    ["Procedures",          (d.procedures || []).join(", ")],
    ["Total Amount",        d.total_amount != null ? `₹${formatNum(d.total_amount)}` : ""],
    ["Doctor Signature",    d.doctor_signature_present == null ? "" : d.doctor_signature_present ? "✅ Present" : "❌ Absent"],
    ["Hospital Stamp",      d.hospital_stamp_present == null ? "" : d.hospital_stamp_present ? "✅ Present" : "❌ Absent"],
  ].filter(([, v]) => v && v !== "");

  const billItems = Object.entries(d.bill_items || {});

  const fieldsHTML = fields.map(([label, val]) => `
    <div class="extract-field">
      <div class="extract-field-label">${label}</div>
      <div class="extract-field-value">${val}</div>
    </div>`).join("");

  const billHTML = billItems.length ? `
    <div style="margin-top:12px">
      <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);margin-bottom:8px">Bill Items</div>
      ${billItems.map(([k, v]) => `
        <div style="display:flex;justify-content:space-between;font-size:12px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
          <span style="color:var(--text-secondary)">${formatKey(k)}</span>
          <span style="font-weight:600">₹${formatNum(v)}</span>
        </div>`).join("")}
    </div>` : "";

  const notesHTML = data.notes ? `
    <div style="margin-top:10px;font-size:11px;color:var(--text-muted);border-top:1px solid rgba(255,255,255,0.06);padding-top:8px">
      ⚠️ ${data.notes}
    </div>` : "";

  panel.innerHTML = `
    <div class="extract-success-panel">
      <div class="extract-header">
        <div style="display:flex;align-items:center;gap:10px">
          <span style="font-size:16px">✅</span>
          <div>
            <div style="font-weight:700;font-size:13px;color:var(--success)">Extraction Complete</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:1px">Powered by Gemini 2.0 Flash Vision · ${data.filename}</div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <span class="extract-doc-type-badge">${(data.document_type || "unknown").replace("_", " ")}</span>
          <div class="extract-confidence-bar">
            <div style="width:60px;height:4px;background:var(--border);border-radius:99px;overflow:hidden">
              <div style="height:100%;width:${confPct}%;background:${confColor};border-radius:99px"></div>
            </div>
            <span style="color:${confColor};font-weight:600">${confPct}% confidence</span>
          </div>
        </div>
      </div>

      ${fields.length > 0 ? `<div class="extract-field-grid">${fieldsHTML}</div>` : ""}
      ${billHTML}
      ${notesHTML}

      <!-- JSON Viewer -->
      <div style="margin-top:12px">
        <button type="button"
          onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display==='none' ? 'block' : 'none'; this.textContent = this.textContent.includes('Show') ? '🔼 Hide Extracted JSON' : '🔽 Show Extracted JSON'"
          style="background:none;border:1px solid var(--border);color:var(--text-muted);border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;margin-bottom:6px">
          🔽 Show Extracted JSON
        </button>
        <div style="display:none">
          <pre style="font-size:10px;background:rgba(0,0,0,0.3);border:1px solid var(--border);border-radius:8px;padding:12px;overflow:auto;max-height:300px;color:var(--text-secondary);white-space:pre-wrap;word-break:break-all">${JSON.stringify(data, null, 2)}</pre>
        </div>
      </div>

      <button type="button" class="btn btn-ghost btn-sm fill-auto-btn" onclick="autoFillFromExtraction()">
        ⬇ Auto-fill form from extracted data
      </button>
    </div>`;
}

function autoFillFromExtraction() {
  // Guard: no extraction done yet
  if (!_lastExtraction) {
    showToast("No extraction data available. Please extract the document first.", "error");
    return;
  }

  const d = _lastExtraction.extracted_data || {};
  let filled = 0;

  // Helper to safely set a field
  function setField(id, value) {
    if (!value || value === "") return;
    const el = document.getElementById(id);
    if (el) { el.value = value; filled++; }
  }

  // Helper to convert any date format → YYYY-MM-DD (required by HTML date input)
  function normalizeDate(raw) {
    if (!raw || raw === "") return "";
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw; // already YYYY-MM-DD

    const mon = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",
                  jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };

    // DD-Mon-YYYY  e.g. "01-Nov-2024"
    let m = raw.match(/^(\d{1,2})[-\/\s]([A-Za-z]{3,9})[-\/\s](\d{4})$/);
    if (m) { const mo=mon[m[2].slice(0,3).toLowerCase()]; if(mo) return `${m[3]}-${mo}-${m[1].padStart(2,"0")}`; }

    // DD/MM/YYYY
    m = raw.match(/^(\d{1,2})[-\/](\d{1,2})[-\/](\d{4})$/);
    if (m) return `${m[3]}-${m[2].padStart(2,"0")}-${m[1].padStart(2,"0")}`;

    // "November 1, 2024" or "1 November 2024"
    m = raw.match(/(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})/);
    if (m) { const mo=mon[m[2].slice(0,3).toLowerCase()]; if(mo) return `${m[3]}-${mo}-${m[1].padStart(2,"0")}`; }
    m = raw.match(/([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})/);
    if (m) { const mo=mon[m[1].slice(0,3).toLowerCase()]; if(mo) return `${m[3]}-${mo}-${m[2].padStart(2,"0")}`; }

    const p = new Date(raw);
    return isNaN(p) ? raw : p.toISOString().split("T")[0];
  }

  // ── Map extracted fields → form fields ─────────────────────────────────
  setField("memberName",    d.patient_name);
  setField("memberId",      d.member_id);               // ← Employee / Member ID
  setField("hospital",      d.hospital_name);
  setField("doctorName",    d.doctor_name);
  setField("doctorReg",     d.doctor_registration);
  setField("diagnosis",     d.diagnosis);
  setField("treatment",     d.treatment);

  // Date: convert "01-Nov-2024" → "2024-11-01" before setting input[type=date]
  const normDate = normalizeDate(d.treatment_date);
  setField("treatmentDate", normDate);                  // ← Fixed date format


  // Helper: Gemini may return medicines/tests as a string or an array — normalise both
  function toArray(v) {
    if (!v) return [];
    if (Array.isArray(v)) return v.filter(Boolean);
    if (typeof v === "string") return v.split(/[,;\n]+/).map(s => s.trim()).filter(Boolean);
    return [];
  }

  const medicines  = toArray(d.medicines_prescribed);
  const tests      = toArray(d.tests_prescribed);
  const procedures = toArray(d.procedures);

  if (medicines.length)  { setField("medicines",      medicines.join(", ")); }
  if (tests.length)      { setField("testsPrescribed", tests.join(", ")); }
  if (procedures.length) { setField("procedures",      procedures.join(", ")); }

  // Fill bill items
  const billItems = d.bill_items || {};
  const billEntries = Object.entries(billItems).filter(([, v]) => v !== null && v !== undefined);
  if (billEntries.length) {
    const container = document.getElementById("billItemsContainer");
    if (container) {
      container.innerHTML = "";
      billEntries.forEach(([k, v]) => {
        const row = document.createElement("div");
        row.className = "bill-item-row";
        row.style.cssText = "display:grid;grid-template-columns:1fr 1fr auto;gap:12px;margin-bottom:10px;align-items:center";
        row.innerHTML = `
          <input type="text" class="bill-item-key" value="${k}" placeholder="Item" />
          <input type="number" class="bill-item-val" value="${v}" placeholder="Amount (₹)" step="0.01" />
          <button type="button" class="btn btn-secondary btn-sm" onclick="removeBillRow(this)" style="width:36px;height:36px;padding:0;display:flex;align-items:center;justify-content:center">✕</button>`;
        container.appendChild(row);
        filled++;
      });
    }
  }

  // Fill total_amount into claim amount whenever it's available
  if (d.total_amount != null && d.total_amount !== "") {
    setField("claimAmount", String(d.total_amount));
  }

  if (filled === 0) {
    showToast("No fields could be extracted from this document. Please fill the form manually.", "info");
  } else {
    showToast(`✅ Auto-filled ${filled} field${filled !== 1 ? "s" : ""} from extracted document data!`, "success");
  }
}

// ─── Utilities ───────────────────────────────────────────────

async function apiFetch(url, opts = {}) {
  // Do NOT force Content-Type for FormData (browser sets it with boundary)
  const isFormData = opts.body instanceof FormData;
  const res = await fetch(API + url, {
    ...(!isFormData && { headers: { "Content-Type": "application/json" } }),
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function showToast(msg, type = "info") {
  const container = document.getElementById("toastContainer");
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function formatNum(n) {
  if (n == null || isNaN(n)) return "0";
  return Number(n).toLocaleString("en-IN");
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function formatKey(k) {
  return k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function decisionIcon(d) {
  return { APPROVED: "✅", REJECTED: "❌", PARTIAL: "🔶", MANUAL_REVIEW: "🔵" }[d] || "⬜";
}

function decisionBigIcon(d) {
  return { APPROVED: "✅", REJECTED: "🚫", PARTIAL: "🔶", MANUAL_REVIEW: "🔍" }[d] || "⬜";
}

function confidencePill(score) {
  const pct = Math.round((score || 0) * 100);
  const color = pct >= 85 ? "var(--success)" : pct >= 70 ? "var(--warning)" : "var(--error)";
  return `<span style="font-family:'Outfit',sans-serif;font-weight:600;color:${color}">${pct}%</span>`;
}

function rejectionDesc(code) {
  const map = {
    POLICY_INACTIVE:        "Policy not active on treatment date",
    WAITING_PERIOD:         "Treatment falls within the waiting period",
    MEMBER_NOT_COVERED:     "Claimant not found in policy records",
    MISSING_DOCUMENTS:      "Required documents not submitted",
    ILLEGIBLE_DOCUMENTS:    "Documents are not readable",
    INVALID_PRESCRIPTION:   "Prescription is missing or invalid",
    DOCTOR_REG_INVALID:     "Doctor registration number invalid or missing",
    DATE_MISMATCH:          "Document dates do not match",
    PATIENT_MISMATCH:       "Patient details do not match records",
    SERVICE_NOT_COVERED:    "Treatment or service is not covered under policy",
    EXCLUDED_CONDITION:     "Condition is in the exclusions list",
    PRE_AUTH_MISSING:       "Pre-authorization was required but not obtained",
    ANNUAL_LIMIT_EXCEEDED:  "Annual coverage limit has been exhausted",
    SUB_LIMIT_EXCEEDED:     "Category sub-limit has been exceeded",
    PER_CLAIM_EXCEEDED:     "Single claim amount exceeds the per-claim limit",
    NOT_MEDICALLY_NECESSARY:"Treatment is not medically justified by the diagnosis",
    EXPERIMENTAL_TREATMENT: "Treatment is experimental or unproven",
    COSMETIC_PROCEDURE:     "Cosmetic or aesthetic procedure — not covered",
    LATE_SUBMISSION:        "Claim submitted after the 30-day deadline",
    DUPLICATE_CLAIM:        "Same treatment has already been claimed",
    BELOW_MIN_AMOUNT:       "Claim amount is below the ₹500 minimum",
  };
  return map[code] || code;
}

// ─── Approved Amount Cell ─────────────────────────────────────
function approvedAmountCell(decision, amount) {
  if (decision === "REJECTED")      return `<span style="color:var(--error);font-weight:600">₹0</span>`;
  if (decision === "MANUAL_REVIEW") return `<span style="color:var(--warning);font-weight:600">Pending</span>`;
  return `₹${formatNum(amount || 0)}`;
}

// ─── Download Decision Report (PDF) ──────────────────────────
async function downloadDecisionReport() {
  // Load jsPDF from global (loaded via CDN in index.html)
  const { jsPDF } = window.jspdf;
  if (!jsPDF) { showToast("PDF library not loaded yet. Try again.", "error"); return; }

  // Fetch current claim from API (it's stored after openClaim)
  const claimId = document.querySelector(".decision-banner")?.closest("[data-claim-id]")
                    ?.dataset?.claimId;

  // Read from the currently-rendered DOM instead
  const decisionEl   = document.querySelector(".decision-text");
  const memberName   = document.querySelector(".decision-banner ~ .grid-3 .card:nth-child(2) strong")?.textContent || "";
  const memberId     = document.querySelector(".decision-banner ~ .grid-3 .card:nth-child(2)")?.textContent?.match(/ID: (\S+)/)?.[1] || "";
  const txDate       = document.querySelector(".decision-banner ~ .grid-3 .card:nth-child(2)")?.textContent?.match(/Treatment: (\S+)/)?.[1] || "";
  const decisionText = decisionEl?.textContent?.trim() || "—";
  const amountEls    = document.querySelectorAll(".decision-amount");
  const approvedAmt  = amountEls?.[0]?.textContent?.trim() || "—";
  const claimedAmt   = document.querySelector(".decision-banner")?.textContent?.match(/Claimed: ([\d,₹]+)/)?.[1] || "—";

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const PW = doc.internal.pageSize.getWidth();

  // ── Header ──────────────────────────────────────────────────
  doc.setFillColor(79, 70, 229);   // indigo
  doc.rect(0, 0, PW, 28, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.text("Plum OPD — Claim Decision Report", 14, 12);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`Generated: ${new Date().toLocaleString("en-IN")}  |  Policy: PLUM_OPD_2024`, 14, 22);
  doc.setTextColor(0, 0, 0);

  let y = 36;

  // ── Decision Banner ─────────────────────────────────────────
  const bColor = decisionText === "APPROVED" ? [16,185,129]
               : decisionText === "REJECTED"  ? [239,68,68]
               : decisionText === "PARTIAL"   ? [249,115,22]
               :                                [59,130,246];
  doc.setFillColor(...bColor);
  doc.roundedRect(14, y, PW - 28, 22, 3, 3, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(15);
  doc.setFont("helvetica", "bold");
  const icon = {APPROVED:"✓", REJECTED:"✗", PARTIAL:"◑", MANUAL_REVIEW:"?"}[decisionText] || "•";
  doc.text(`${icon}  ${decisionText.replace("_"," ")}`, 20, y + 9);
  doc.setFontSize(10);
  doc.text(`Approved: ${approvedAmt}`, PW - 60, y + 7);
  doc.text(`Claimed:  ${claimedAmt}`, PW - 60, y + 14);
  doc.setTextColor(0, 0, 0);
  y += 30;

  // ── Claim Details ───────────────────────────────────────────
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.setFillColor(240, 242, 255);
  doc.rect(14, y, PW - 28, 8, "F");
  doc.text("Claim Details", 16, y + 5.5);
  y += 12;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);

  const details = [
    ["Member Name",     memberName || "—"],
    ["Member ID",       memberId   || "—"],
    ["Treatment Date",  txDate     || "—"],
    ["Decision",        decisionText],
    ["Approved Amount", approvedAmt],
  ];
  details.forEach(([k, v]) => {
    doc.setFont("helvetica", "bold"); doc.text(k + ":", 16, y);
    doc.setFont("helvetica", "normal"); doc.text(String(v), 75, y);
    y += 7;
  });
  y += 4;

  // ── Audit Trail ─────────────────────────────────────────────
  const auditSteps = document.querySelectorAll(".audit-step");
  if (auditSteps.length) {
    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");
    doc.setFillColor(240, 242, 255);
    doc.rect(14, y, PW - 28, 8, "F");
    doc.text("Decision Audit Trail", 16, y + 5.5);
    y += 12;

    const rows = [];
    auditSteps.forEach(step => {
      const name   = step.querySelector(".audit-step-name")?.textContent?.trim() || "";
      const passed = step.classList.contains("passed");
      const detail = step.querySelector(".audit-step-detail")?.textContent?.trim() || "";
      rows.push([passed ? "✓ PASS" : "✗ FAIL", name, detail.substring(0, 60)]);
    });

    doc.autoTable({
      startY: y,
      head: [["Result", "Step", "Details"]],
      body: rows,
      theme: "grid",
      headStyles: { fillColor: [79, 70, 229], textColor: 255, fontStyle: "bold", fontSize: 9 },
      bodyStyles: { fontSize: 8 },
      columnStyles: { 0: { cellWidth: 20 }, 1: { cellWidth: 55 }, 2: { cellWidth: 95 } },
      margin: { left: 14, right: 14 },
      didParseCell: (data) => {
        if (data.column.index === 0 && data.section === "body") {
          data.cell.styles.textColor = data.cell.raw?.startsWith("✓") ? [16,185,129] : [239,68,68];
          data.cell.styles.fontStyle = "bold";
        }
      },
    });
    y = doc.lastAutoTable.finalY + 8;
  }

  // ── Rejection Reasons ────────────────────────────────────────
  const codes = document.querySelectorAll(".code-pill");
  if (codes.length) {
    if (y > 240) { doc.addPage(); y = 20; }
    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");
    doc.setFillColor(255, 235, 235);
    doc.rect(14, y, PW - 28, 8, "F");
    doc.text("Rejection Codes", 16, y + 5.5);
    y += 12;
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    const codeList = [...new Set([...codes].map(c => c.textContent.trim()))];
    codeList.forEach(c => { doc.text("• " + c, 18, y); y += 6; });
    y += 4;
  }

  // ── Footer ───────────────────────────────────────────────────
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.text(`Plum OPD Claim Adjudication System  |  Page ${i} of ${pageCount}  |  Confidential`, 14, 290);
    doc.setTextColor(0, 0, 0);
  }

  const filename = `Plum_Decision_Report_${new Date().toISOString().split("T")[0]}.pdf`;
  doc.save(filename);
  showToast(`📥 Report downloaded: ${filename}`, "success");
}

// ─── Boot ────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  showPage("dashboard");
});
