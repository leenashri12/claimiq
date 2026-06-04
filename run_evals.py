"""
Standalone Evaluation Script
Runs all 10 test cases from test_cases.json through the adjudication engine
and prints a pass/fail report — no server required.

Usage:
    python run_evals.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from app.adjudication import adjudicate_claim


def fmt(n):
    return f"Rs.{n:,.0f}" if n is not None else "N/A"


def run_evals():
    test_cases = json.loads((ROOT / "test_cases.json").read_text())["test_cases"]

    print()
    print("=" * 70)
    print("  PLUM OPD CLAIM ADJUDICATION - TEST EVALUATION REPORT")
    print("=" * 70)

    results = []
    for tc in test_cases:
        input_data = tc["input_data"]
        expected   = tc["expected_output"]

        result = adjudicate_claim(
            input_data,
            previous_claims_same_day=input_data.get("previous_claims_same_day", 0),
            claims_ytd_amount=0,
        )

        exp_dec = expected.get("decision", "")
        act_dec = result["decision"]
        dec_ok  = act_dec == exp_dec

        exp_amt = expected.get("approved_amount")
        act_amt = result.get("approved_amount")
        amt_ok  = True
        if exp_amt is not None and act_amt is not None:
            amt_ok = abs(float(exp_amt) - float(act_amt)) <= 150

        passed = dec_ok and amt_ok
        results.append(passed)

        icon = "[PASS]" if passed else "[FAIL]"
        print(f"\n  {icon}  |  {tc['case_id']} -- {tc['case_name']}")
        print(f"         |  Decision   : Expected={exp_dec:<15} Got={act_dec} {'OK' if dec_ok else 'MISMATCH'}")
        if exp_amt is not None:
            print(f"         |  Amount     : Expected={fmt(exp_amt):<12} Got={fmt(act_amt)} {'OK' if amt_ok else 'MISMATCH'}")
        print(f"         |  Confidence : {round(result['confidence_score'] * 100)}%")

        # Audit trail summary
        for step in result["audit_trail"]:
            marker = "  OK" if step["passed"] else "  !!"
            print(f"         |  {marker} Step {step['step']}: {step['name']}")

        if result["rejection_reasons"]:
            print(f"         |  Rejections : {', '.join(result['rejection_reasons'])}")

    pass_count = sum(results)
    total      = len(results)
    pct        = round(pass_count / total * 100)

    print()
    print("=" * 70)
    print(f"  RESULT: {pass_count}/{total} tests passed ({pct}%)")
    bar_filled = "#" * (pass_count * 2)
    bar_empty  = "." * ((total - pass_count) * 2)
    print(f"  [{bar_filled}{bar_empty}]")
    print("=" * 70)
    print()

    return pass_count == total


if __name__ == "__main__":
    success = run_evals()
    sys.exit(0 if success else 1)
