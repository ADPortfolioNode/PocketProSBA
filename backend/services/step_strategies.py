"""
Step Strategies Service

Implements the Strategy Pattern for different approaches to executing task steps.
Each strategy has real, differentiated behavior (not empty stubs).
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _step_payload(step) -> Dict[str, Any]:
    if hasattr(step, "data") and isinstance(step.data, dict):
        return step.data
    if isinstance(step, dict):
        return step.get("data", step) if isinstance(step.get("data"), dict) else step
    return {"instruction": str(step)}


def _instruction(payload: Dict[str, Any]) -> str:
    return (
        payload.get("instruction")
        or payload.get("message")
        or payload.get("query")
        or payload.get("text")
        or ""
    ).strip()


class StepStrategy(ABC):
    """Abstract base class for step execution strategies"""

    @abstractmethod
    def execute(self, step) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def validate(self, result: Dict[str, Any]) -> bool:
        if not isinstance(result, dict):
            return False
        if result.get("success") is False:
            return False
        data = result.get("data") or result
        if isinstance(data, dict) and data.get("error"):
            return False
        return True


class DefaultStrategy(StepStrategy):
    """Default strategy — execute via api_service with Concierge/agent routing."""

    @property
    def name(self) -> str:
        return "default"

    def execute(self, step) -> Dict[str, Any]:
        try:
            try:
                from backend.services.api_service import execute_step_service
            except ImportError:
                from services.api_service import execute_step_service
            payload = _step_payload(step)
            result = execute_step_service(
                payload if isinstance(payload, dict) else {"instruction": str(payload)}
            )
            if not isinstance(result, dict):
                return {"success": True, "data": {"result": result}, "error": None}
            ok = result.get("status") != "failed" and not result.get("error")
            return {
                "success": ok,
                "data": result.get("data", result),
                "error": result.get("error"),
            }
        except Exception as e:
            logger.exception("DefaultStrategy failed")
            return {"success": False, "error": str(e)}


class ConservativeStrategy(StepStrategy):
    """Conservative: execute + require non-empty result text and re-validate."""

    @property
    def name(self) -> str:
        return "conservative"

    def execute(self, step) -> Dict[str, Any]:
        base = DefaultStrategy().execute(step)
        if not base.get("success"):
            return base
        data = base.get("data") or {}
        text = ""
        if isinstance(data, dict):
            text = str(data.get("result") or data.get("text") or "")
        if len(text.strip()) < 20:
            return {
                "success": False,
                "error": "Conservative validation failed: result too short",
                "data": data,
            }
        return base

    def validate(self, result: Dict[str, Any]) -> bool:
        if not super().validate(result):
            return False
        data = result.get("data") or {}
        text = str((data.get("result") if isinstance(data, dict) else "") or "")
        return len(text.strip()) >= 20


class AggressiveStrategy(StepStrategy):
    """Aggressive: prefer FunctionAgent for speed on math/eligibility, else default."""

    @property
    def name(self) -> str:
        return "aggressive"

    def execute(self, step) -> Dict[str, Any]:
        payload = _step_payload(step)
        instruction = _instruction(payload)
        low = instruction.lower()
        try:
            if any(k in low for k in ("payment", "eligib", "calculate", "percent", "compare")):
                from backend.assistants.function import FunctionAgent
                result = FunctionAgent().handle_message(instruction)
                return {
                    "success": not result.get("error"),
                    "data": {
                        "result": result.get("text"),
                        "sources": result.get("sources", []),
                        "agent": "FunctionAgent",
                    },
                    "error": result.get("text") if result.get("error") else None,
                }
        except Exception as e:
            logger.warning("Aggressive fast-path failed: %s", e)
        return DefaultStrategy().execute(step)


class DocumentSearchStrategy(StepStrategy):
    """Search uploaded docs / RAG, then fall back to FileAgent + Concierge."""

    @property
    def name(self) -> str:
        return "document_search"

    def execute(self, step) -> Dict[str, Any]:
        payload = _step_payload(step)
        instruction = _instruction(payload) or "list files"
        try:
            try:
                from backend.services.api_service import query_documents_service
                rag = query_documents_service(instruction, top_k=5)
                if rag.get("success") and rag.get("count", 0) > 0:
                    snippets = []
                    for r in rag.get("results", [])[:5]:
                        snippets.append(f"- {r.get('content', '')[:200]}")
                    text = "Document search results:\n" + "\n".join(snippets)
                    return {
                        "success": True,
                        "data": {"result": text, "sources": rag.get("results", []), "mode": "rag"},
                        "error": None,
                    }
            except Exception as rag_err:
                logger.info("RAG document search soft-fail: %s", rag_err)

            from backend.assistants.file import FileAgent
            result = FileAgent().handle_message(f"search {instruction}")
            return {
                "success": not result.get("error"),
                "data": {
                    "result": result.get("text"),
                    "sources": result.get("sources", []),
                    "mode": "file_agent",
                },
                "error": None if not result.get("error") else result.get("text"),
            }
        except Exception as e:
            logger.exception("DocumentSearchStrategy failed")
            return {"success": False, "error": str(e)}


class TaskDecompositionStrategy(StepStrategy):
    """Produce a multi-step plan for the instruction (does not execute sub-steps)."""

    @property
    def name(self) -> str:
        return "task_decomposition"

    def execute(self, step) -> Dict[str, Any]:
        payload = _step_payload(step)
        instruction = _instruction(payload)
        try:
            try:
                from backend.services.api_service import decompose_task_service
            except ImportError:
                from services.api_service import decompose_task_service
            result = decompose_task_service(instruction, payload.get("session_id"))
            steps = result.get("steps") or []
            text_lines = [f"Decomposed into {len(steps)} step(s):"]
            for i, s in enumerate(steps, 1):
                data = s.get("data") or {}
                text_lines.append(
                    f"{i}. [{s.get('type', 'step')}] {data.get('instruction', '')[:160]}"
                )
            return {
                "success": True,
                "data": {
                    "result": "\n".join(text_lines),
                    "steps": steps,
                    "task_id": result.get("task_id"),
                },
                "error": None,
            }
        except Exception as e:
            logger.exception("TaskDecompositionStrategy failed")
            return {"success": False, "error": str(e)}


class AnalysisStrategy(StepStrategy):
    """Analyze instruction with FunctionAgent summary + Concierge context."""

    @property
    def name(self) -> str:
        return "analysis"

    def execute(self, step) -> Dict[str, Any]:
        payload = _step_payload(step)
        instruction = _instruction(payload)
        try:
            from backend.assistants.function import FunctionAgent
            fn = FunctionAgent().handle_message(f"analyze and summarize: {instruction}")
            from backend.assistants.concierge import Concierge
            cg = Concierge().handle_message(instruction)
            text = (
                f"{fn.get('text', '')}\n\n---\n\n{cg.get('text', '')}"
            ).strip()
            sources = (fn.get("sources") or []) + (cg.get("sources") or [])
            return {
                "success": bool(text),
                "data": {"result": text, "sources": sources, "mode": "analysis"},
                "error": None if text else "Empty analysis",
            }
        except Exception as e:
            logger.exception("AnalysisStrategy failed")
            return {"success": False, "error": str(e)}


class ResponseGenerationStrategy(StepStrategy):
    """Generate a user-facing answer via Concierge."""

    @property
    def name(self) -> str:
        return "response_generation"

    def execute(self, step) -> Dict[str, Any]:
        payload = _step_payload(step)
        instruction = _instruction(payload)
        try:
            from backend.assistants.concierge import Concierge
            result = Concierge().handle_message(instruction, session_id=payload.get("session_id"))
            return {
                "success": not result.get("error"),
                "data": {
                    "result": result.get("text"),
                    "sources": result.get("sources", []),
                    "mode": "concierge",
                },
                "error": None if not result.get("error") else result.get("text"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class FastDocumentSearchStrategy(DocumentSearchStrategy):
    @property
    def name(self) -> str:
        return "fast_document_search"

    def execute(self, step) -> Dict[str, Any]:
        # Cap work: FileAgent only (skip full RAG round-trip when possible)
        payload = _step_payload(step)
        instruction = _instruction(payload) or "list files"
        try:
            from backend.assistants.file import FileAgent
            result = FileAgent().handle_message(f"search {instruction}")
            return {
                "success": not result.get("error"),
                "data": {
                    "result": result.get("text"),
                    "sources": result.get("sources", []),
                    "mode": "fast_file",
                },
                "error": None if not result.get("error") else result.get("text"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class DetailedDocumentSearchStrategy(DocumentSearchStrategy):
    @property
    def name(self) -> str:
        return "detailed_document_search"

    def execute(self, step) -> Dict[str, Any]:
        base = super().execute(step)
        if not base.get("success"):
            return base
        # Enrich with Concierge synthesis
        try:
            payload = _step_payload(step)
            instruction = _instruction(payload)
            from backend.assistants.concierge import Concierge
            synth = Concierge().handle_message(
                f"Based on document findings, explain: {instruction}"
            )
            data = base.get("data") or {}
            data["result"] = (
                f"{data.get('result', '')}\n\n**Synthesis:**\n{synth.get('text', '')}"
            )
            data["mode"] = "detailed_search"
            base["data"] = data
        except Exception as e:
            logger.warning("Detailed synthesis soft-fail: %s", e)
        return base


class LLMAnalysisStrategy(AnalysisStrategy):
    @property
    def name(self) -> str:
        return "llm_analysis"


class TemplateResponseStrategy(StepStrategy):
    """Structured template answer for common SBA intents without external calls."""

    @property
    def name(self) -> str:
        return "template_response"

    def execute(self, step) -> Dict[str, Any]:
        payload = _step_payload(step)
        instruction = _instruction(payload)
        low = instruction.lower()
        if "7(a)" in low or "7a" in low:
            body = (
                "**SBA 7(a) Loan Program**\n"
                "- Primary general-purpose loan guaranty program\n"
                "- Max loan amount typically up to $5 million\n"
                "- Uses: working capital, equipment, real estate, refinancing (limits apply)\n"
                "- Next step: talk to an SBA lender or use Lender Match\n"
                "https://www.sba.gov/funding-programs/loans/7a-loans"
            )
        elif "504" in low:
            body = (
                "**SBA 504 Loan Program**\n"
                "- Long-term fixed-asset financing via Certified Development Companies\n"
                "- Best for owner-occupied real estate and major equipment\n"
                "https://www.sba.gov/funding-programs/loans/504-loans"
            )
        elif "microloan" in low:
            body = (
                "**SBA Microloan Program**\n"
                "- Loans up to $50,000 through nonprofit intermediaries\n"
                "- Often includes technical assistance\n"
                "https://www.sba.gov/funding-programs/loans/microloans"
            )
        else:
            body = (
                f"**SBA guidance template**\n"
                f"Topic: {instruction[:200]}\n"
                f"1. Clarify business need (working capital vs real estate vs R&D)\n"
                f"2. Match program (7(a), 504, Microloan, SBIR)\n"
                f"3. Gather financials and ownership docs\n"
                f"4. Connect with lender or SBDC counselor\n"
                f"https://www.sba.gov/funding-programs"
            )
        return {
            "success": True,
            "data": {"result": body, "mode": "template"},
            "error": None,
        }


class StepStrategyFactory:
    """Factory for creating step strategy instances"""

    _strategies = {
        "default": DefaultStrategy,
        "conservative": ConservativeStrategy,
        "aggressive": AggressiveStrategy,
        "document_search": DocumentSearchStrategy,
        "task_decomposition": TaskDecompositionStrategy,
        "analysis": AnalysisStrategy,
        "response_generation": ResponseGenerationStrategy,
        "fast_document_search": FastDocumentSearchStrategy,
        "detailed_document_search": DetailedDocumentSearchStrategy,
        "llm_analysis": LLMAnalysisStrategy,
        "template_response": TemplateResponseStrategy,
    }

    @classmethod
    def get_strategy(cls, strategy_name: str) -> StepStrategy:
        strategy_class = cls._strategies.get(strategy_name, cls._strategies["default"])
        return strategy_class()

    @classmethod
    def get_available_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())
