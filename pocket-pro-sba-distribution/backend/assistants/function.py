"""
FunctionAgent — executable helper tools for SBA-related calculations and analysis.
"""
from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import BaseAssistant

logger = logging.getLogger(__name__)


class FunctionAgent(BaseAssistant):
    """Runs concrete helper functions (loan math, eligibility cues, summaries)."""

    def __init__(self):
        super().__init__("FunctionAgent")

    def handle_message(self, message, session_id=None, metadata=None):
        try:
            self._update_status("processing", 20, "Selecting function…")
            text = (message or "").strip()
            if not text:
                return self.report_failure("No instruction provided to FunctionAgent.")

            intent = self._classify(text)
            self._update_status("processing", 60, f"Running {intent}…")

            if intent == "loan_payment":
                result = self._loan_payment(text)
            elif intent == "eligibility":
                result = self._eligibility_checklist(text)
            elif intent == "compare_loans":
                result = self._compare_loan_programs(text)
            elif intent == "summarize":
                result = self._summarize(text)
            elif intent == "percent":
                result = self._percent_math(text)
            else:
                result = self._general_analysis(text)

            self._update_status("completed", 100, "Function complete")
            return self.report_success(
                text=result["text"],
                sources=result.get("sources", []),
                additional_data={
                    "function": intent,
                    "computed": result.get("computed"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as e:
            logger.exception("FunctionAgent failed")
            return self.report_failure(f"FunctionAgent error: {e}")

    def _classify(self, text: str) -> str:
        low = text.lower()
        if any(k in low for k in ("payment", "monthly", "amortiz", "interest rate", "apr")):
            return "loan_payment"
        if any(k in low for k in ("eligib", "qualify", "requirements", "do i qualify")):
            return "eligibility"
        if any(k in low for k in ("compare", "vs", "versus", "difference between", "7(a)", "7a", "504", "microloan")):
            return "compare_loans"
        if any(k in low for k in ("summarize", "summary", "analyze and summarize", "organize findings")):
            return "summarize"
        if any(k in low for k in ("percent", "%", "of ", "calculate", "compute")):
            return "percent"
        return "general"

    def _extract_numbers(self, text: str) -> List[float]:
        # $250,000 or 250000 or 6.5%
        found = re.findall(r"\$?\s*([\d,]+(?:\.\d+)?)\s*%?", text)
        nums = []
        for f in found:
            try:
                nums.append(float(f.replace(",", "")))
            except ValueError:
                continue
        return nums

    def _loan_payment(self, text: str) -> Dict[str, Any]:
        nums = self._extract_numbers(text)
        # Heuristic: principal (largest money-like), rate %, years
        principal = 100000.0
        annual_rate = 0.085
        years = 10
        if nums:
            # Prefer a large number as principal
            moneyish = [n for n in nums if n >= 1000]
            if moneyish:
                principal = max(moneyish)
            rates = [n for n in nums if 0 < n < 40]
            if rates:
                annual_rate = rates[0] / 100.0 if rates[0] > 1 else rates[0]
            # years: small integer-like, not the principal and not the rate
            rate_val = rates[0] if rates else None
            for n in nums:
                if 1 <= n <= 40 and n != principal and (rate_val is None or n != rate_val):
                    years = int(n)
                    break

        monthly_rate = annual_rate / 12.0
        n_payments = max(int(years * 12), 1)
        if monthly_rate <= 0:
            payment = principal / n_payments
        else:
            payment = principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / (
                (1 + monthly_rate) ** n_payments - 1
            )
        total_paid = payment * n_payments
        interest = total_paid - principal

        text_out = (
            f"**Estimated loan payment**\n\n"
            f"- Principal: ${principal:,.2f}\n"
            f"- Annual rate: {annual_rate * 100:.2f}%\n"
            f"- Term: {years} years ({n_payments} months)\n"
            f"- **Monthly payment: ${payment:,.2f}**\n"
            f"- Total paid: ${total_paid:,.2f}\n"
            f"- Estimated interest: ${interest:,.2f}\n\n"
            f"_Estimates only — actual SBA rates/terms depend on lender and program._"
        )
        return {
            "text": text_out,
            "computed": {
                "principal": principal,
                "annual_rate": annual_rate,
                "years": years,
                "monthly_payment": round(payment, 2),
                "total_paid": round(total_paid, 2),
                "interest": round(interest, 2),
            },
            "sources": [{"title": "SBA loan programs", "url": "https://www.sba.gov/funding-programs/loans"}],
        }

    def _eligibility_checklist(self, text: str) -> Dict[str, Any]:
        low = text.lower()
        checks = [
            ("Operate for profit (generally)", True),
            ("Meet SBA size standards for your industry", "size" not in low or "small" in low),
            ("Business is in the U.S.", True),
            ("Owner invests reasonable equity", True),
            ("Good personal/business credit history", "credit" not in low or "good" in low),
            ("Use of proceeds is eligible (not speculative)", "casino" not in low and "gambling" not in low),
        ]
        lines = ["**SBA financing eligibility checklist (general guidance)**\n"]
        for label, ok in checks:
            lines.append(f"- {'✅' if ok else '⚠️'} {label}")
        lines.append(
            "\nThis is not a formal eligibility determination. "
            "A lender or [Lender Match](https://www.sba.gov/funding-programs/loans/lender-match) can assess your case."
        )
        return {
            "text": "\n".join(lines),
            "computed": {"checks": [{"label": l, "pass": bool(p)} for l, p in checks]},
            "sources": [
                {"title": "SBA 7(a) loans", "url": "https://www.sba.gov/funding-programs/loans/7a-loans"},
                {"title": "Lender Match", "url": "https://www.sba.gov/funding-programs/loans/lender-match"},
            ],
        }

    def _compare_loan_programs(self, text: str) -> Dict[str, Any]:
        programs = [
            {
                "name": "7(a)",
                "max": "$5 million",
                "use": "Working capital, equipment, real estate, refinancing (with limits)",
                "best_for": "General-purpose financing",
            },
            {
                "name": "504",
                "max": "Up to $5–5.5M project structure",
                "use": "Owner-occupied real estate & major equipment",
                "best_for": "Fixed assets with CDC partner",
            },
            {
                "name": "Microloan",
                "max": "$50,000",
                "use": "Working capital, inventory, supplies, equipment",
                "best_for": "Startups and very small needs",
            },
        ]
        lines = ["**SBA loan program comparison**\n"]
        for p in programs:
            lines.append(f"### {p['name']}")
            lines.append(f"- Typical max: {p['max']}")
            lines.append(f"- Common uses: {p['use']}")
            lines.append(f"- Best for: {p['best_for']}\n")
        lines.append("Source overview: https://www.sba.gov/funding-programs/loans")
        return {
            "text": "\n".join(lines),
            "computed": {"programs": programs},
            "sources": [{"title": "SBA Loans", "url": "https://www.sba.gov/funding-programs/loans"}],
        }

    def _summarize(self, text: str) -> Dict[str, Any]:
        # Pull topic after "about:" / "summarize"
        topic = text
        for sep in ("about:", "related to:", "summarize", "analyze and summarize"):
            if sep in text.lower():
                idx = text.lower().find(sep)
                topic = text[idx + len(sep):].strip(" :-\n") or text
                break
        bullets = [
            f"Focus area: {topic[:200]}",
            "Identify relevant SBA program (7(a), 504, Microloan, SBIR, counseling).",
            "List eligibility and documentation next steps.",
            "Recommend Lender Match or local SBDC counseling when financing is needed.",
        ]
        return {
            "text": "**Analysis summary**\n\n" + "\n".join(f"- {b}" for b in bullets),
            "computed": {"topic": topic[:300], "bullets": bullets},
            "sources": [],
        }

    def _percent_math(self, text: str) -> Dict[str, Any]:
        nums = self._extract_numbers(text)
        if len(nums) >= 2:
            a, b = nums[0], nums[1]
            # "X% of Y" or "X of Y"
            if "%" in text or "percent" in text.lower():
                pct = a if a <= 100 else a
                base = b if b >= a else a
                if a <= 100:
                    value = (a / 100.0) * b
                    formula = f"{a}% of {b:,.2f} = {value:,.2f}"
                else:
                    value = (a / b) * 100 if b else 0
                    formula = f"{a:,.2f} is {value:.2f}% of {b:,.2f}"
            else:
                value = a * b
                formula = f"{a} × {b} = {value}"
            return {"text": f"**Calculation:** {formula}", "computed": {"formula": formula, "value": value}}
        return self._general_analysis(text)

    def _general_analysis(self, text: str) -> Dict[str, Any]:
        words = re.findall(r"[A-Za-z0-9$%().-]+", text)
        return {
            "text": (
                f"FunctionAgent processed your request ({len(words)} tokens).\n\n"
                f"**Request:** {text[:500]}\n\n"
                "I can compute loan payments, eligibility checklists, program comparisons, "
                "percent math, or summaries. Try: “monthly payment on $250000 at 8.5% for 10 years”."
            ),
            "computed": {"token_count": len(words)},
            "sources": [],
        }


# Back-compat alias used by older imports
def create_function_agent() -> FunctionAgent:
    return FunctionAgent()
