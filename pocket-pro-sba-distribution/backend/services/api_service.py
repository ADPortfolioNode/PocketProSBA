import logging
from backend.services.rag import get_rag_manager
from backend.assistants.concierge import Concierge
from backend.assistants.search import SearchAgent

logger = logging.getLogger(__name__)

def get_system_info_service():
    """Get system information"""
    try:
        rag_manager = get_rag_manager()
        
        # Check if RAG manager is available without causing connection issues
        rag_available = False
        collection_stats = {"count": 0}
        
        try:
            rag_available = rag_manager.is_available()
            if rag_available:
                collection_stats = rag_manager.get_collection_stats() or {"count": 0}
        except Exception as rag_error:
            logger.warning(f"RAG system check failed: {str(rag_error)}")
            rag_available = False
        
        return {
            'service': 'PocketPro:SBA Edition',
            'version': '1.0.0',
            'status': 'operational',
            'rag_status': 'available' if rag_available else 'unavailable',
            'vector_store': 'ChromaDB',
            'document_count': collection_stats.get("count", 0)
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {
            'service': 'PocketPro:SBA Edition',
            'version': '1.0.0',
            'status': 'operational',
            'rag_status': 'unavailable',
            'error': 'System information unavailable'
        }

def _build_decomposition_steps(message: str, session_id=None):
    """Rule-based multi-step task plan (functional, no LLM required)."""
    low = (message or "").lower()
    steps = []

    def add(step_type, instruction, agent):
        steps.append({
            "type": step_type,
            "data": {
                "instruction": instruction,
                "suggested_agent_type": agent,
                "session_id": session_id,
            },
        })

    if any(k in low for k in ("loan", "7(a)", "7a", "504", "microloan", "financ")):
        add("document_search", f"Research SBA loan information for: {message}", "SearchAgent")
        add("analysis", f"Analyze eligibility and requirements for: {message}", "FunctionAgent")
        add("response_generation", f"Provide a clear action plan for: {message}", "Concierge")
    elif any(k in low for k in ("file", "document", "upload", "pdf", "read ")):
        add("document_search", f"Locate relevant files for: {message}", "FileAgent")
        add("response_generation", f"Summarize findings for: {message}", "Concierge")
    elif any(k in low for k in ("calculate", "payment", "interest", "percent", "compute")):
        add("analysis", message, "FunctionAgent")
        add("response_generation", f"Explain the calculation result for: {message}", "Concierge")
    elif any(k in low for k in ("business plan", "grant", "sbir", "startup", "marketing")):
        add("document_search", f"Find SBA resources about: {message}", "SearchAgent")
        add("document_search", f"Search local documents about: {message}", "FileAgent")
        add("analysis", f"Organize a step-by-step plan for: {message}", "FunctionAgent")
        add("response_generation", f"Write a concise recommendation for: {message}", "Concierge")
    else:
        add("document_search", f"Gather information about: {message}", "SearchAgent")
        add("response_generation", message, "Concierge")

    return steps


def decompose_task_service(message, session_id):
    """Decompose a user task into executable multi-step plan."""
    try:
        import uuid
        task_id = session_id or str(uuid.uuid4())
        steps = _build_decomposition_steps(message, session_id)

        # Optional concierge preview for the overall ask (non-blocking soft path)
        preview = ""
        sources = []
        try:
            concierge = Concierge()
            response = concierge.handle_message(
                f"Briefly outline how you would help with: {message}",
                session_id=session_id,
            )
            preview = response.get("text", "") or ""
            sources = response.get("sources", [])
        except Exception as preview_err:
            logger.warning("Decompose preview soft-fail: %s", preview_err)
            preview = f"Planned {len(steps)} steps for: {message}"

        return {
            "task_id": task_id,
            "steps": steps,
            "response": {
                "text": preview,
                "sources": sources,
                "steps": steps,
            },
        }
    except Exception as e:
        logger.error(f"Error decomposing task: {str(e)}")
        raise Exception(f"Failed to process message: {str(e)}")


def execute_step_service(task):
    """Execute a decomposed task step using the suggested agent."""
    try:
        step_number = task.get("step_number")
        instruction = (
            task.get("instruction")
            or task.get("message")
            or task.get("query")
            or ""
        )
        agent_type = task.get("suggested_agent_type") or task.get("agent_type") or "Concierge"

        if not instruction:
            raise ValueError("Instruction is required")

        result = None
        agent_used = agent_type

        if agent_type in ("SearchAgent", "search"):
            try:
                agent = SearchAgent()
                result = agent.handle_message(instruction)
            except Exception as e:
                logger.warning("SearchAgent failed (%s); falling back to Concierge", e)
                agent_used = "Concierge"
                result = Concierge().handle_message(instruction)
        elif agent_type in ("FileAgent", "file"):
            from backend.assistants.file import FileAgent
            result = FileAgent().handle_message(instruction)
            agent_used = "FileAgent"
        elif agent_type in ("FunctionAgent", "function"):
            from backend.assistants.function import FunctionAgent
            result = FunctionAgent().handle_message(instruction)
            agent_used = "FunctionAgent"
        else:
            result = Concierge().handle_message(instruction)
            agent_used = "Concierge"

        ok = not (result or {}).get("error")
        return {
            "step_number": step_number,
            "status": "completed" if ok else "failed",
            "result": (result or {}).get("text", ""),
            "sources": (result or {}).get("sources", []),
            "agent": agent_used,
            "success": ok,
            "data": {
                "result": (result or {}).get("text", ""),
                "sources": (result or {}).get("sources", []),
                "agent": agent_used,
            },
        }
    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        raise Exception(f"Failed to execute step: {str(e)}")


def validate_step_service(result, task):
    """Validate a step result with concrete checks."""
    try:
        text = ""
        if isinstance(result, dict):
            text = str(result.get("result") or result.get("text") or "")
            if result.get("error") or result.get("success") is False:
                return {
                    "status": "FAIL",
                    "confidence": 0.15,
                    "feedback": f"Result marked as error: {result.get('error') or 'success=false'}",
                }
        else:
            text = str(result or "")

        if not text or not str(text).strip():
            return {
                "status": "FAIL",
                "confidence": 0.2,
                "feedback": "Step result is empty or invalid",
            }

        stripped = str(text).strip()
        confidence = 0.95 if len(stripped) > 80 else 0.75 if len(stripped) > 20 else 0.45
        status = "PASS" if len(stripped) >= 10 else "FAIL"
        return {
            "status": status,
            "confidence": confidence,
            "feedback": (
                "Step result validated successfully"
                if status == "PASS"
                else "Step result too short to accept"
            ),
            "length": len(stripped),
        }
    except Exception as e:
        logger.error(f"Error validating step: {str(e)}")
        raise Exception(f"Failed to validate step: {str(e)}")

def query_documents_service(query, top_k):
    """Query documents"""
    try:
        rag_manager = get_rag_manager()
        results = rag_manager.query_documents(query, n_results=top_k)
        
        formatted_results = []
        if "documents" in results and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    'id': results["ids"][0][i],
                    'content': doc,
                    'metadata': results["metadatas"][0][i],
                    'distance': results["distances"][0][i] if "distances" in results else 0.0,
                    'relevance_score': 1.0 - (results["distances"][0][i] if "distances" in results else 0.0)
                })
        
        return {
            'success': True,
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        }
    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        raise Exception(f'Search failed: {str(e)}')
