"""
Chat Processing Service
Handles integration between chat routes and Concierge assistant
"""
import logging
import re
import uuid
from datetime import datetime
from backend.assistants.concierge import Concierge

logger = logging.getLogger(__name__)

# Global concierge instance for the application
_concierge_instance = None

def get_concierge():
    """Get or create the Concierge assistant instance"""
    global _concierge_instance
    if _concierge_instance is None:
        try:
            _concierge_instance = Concierge()
            logger.info("Concierge assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Concierge assistant: {str(e)}")
            raise
    return _concierge_instance

def process_chat_message(user_id, message, session_id=None):
    """
    Process a chat message using the Concierge assistant
    
    Args:
        user_id: User identifier
        message: User message content
        session_id: Optional session ID for conversation continuity
    
    Returns:
        dict: Response containing assistant reply and metadata
    """
    try:
        concierge = get_concierge()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Created new session: {session_id}")
        
        # Process the message with Concierge assistant
        result = concierge.handle_message(message, session_id=session_id)

        text = result.get("text") or result.get("response") or ""
        sources = result.get("sources") or []

        # Strip any legacy raw digest appendix if present
        if "Live SBA API notes:" in text:
            text = text.split("Live SBA API notes:")[0].rstrip().rstrip("-").rstrip()

        # Soft-merge live SBA API digests only when the concierge answer is thin.
        # Never append raw digest dumps on top of an already formatted answer.
        try:
            from backend.services.link_enrichment import enrich_answer_with_links

            already_formatted = bool(
                text
                and (
                    "## Links" in text
                    or "clear summary from live SBA" in text.lower()
                    or "Open in Resources" in text
                    or "Official page" in text
                    or re.search(r"\[.+\]\(https?://", text)
                )
            )
            if not already_formatted:
                from backend.routes.rag import _local_kb_sba_answer
                from backend.services.chat_answer_format import (
                    format_hits_as_answer,
                    normalize_hits,
                )
                from pathlib import Path

                kb = _local_kb_sba_answer(message)
                if isinstance(kb, dict) and kb.get("mode") == "sba_api_live":
                    kb_sources = kb.get("source_documents") or kb.get("sources") or []
                    docs, metas = [], []
                    for s in kb_sources:
                        if not isinstance(s, dict):
                            continue
                        meta = s.get("metadata") or {}
                        path = str(meta.get("path") or "")
                        if "manifest" in path:
                            continue
                        body = s.get("content") or ""
                        if path.endswith(".txt"):
                            try:
                                p = Path(path)
                                if p.exists():
                                    body = p.read_text(encoding="utf-8", errors="replace")
                            except Exception:
                                pass
                        docs.append(body)
                        metas.append(
                            {
                                "source": "sba_api",
                                "path": path,
                                "title": meta.get("title") or "",
                            }
                        )
                    hits = normalize_hits(docs, metas)
                    if hits:
                        text, sources = format_hits_as_answer(message, hits)
                    elif not text or len(text) < 80:
                        # Still avoid dumping raw meta-heavy KB text
                        from backend.services.chat_answer_format import format_hits_as_answer as _fmt
                        text, sources = _fmt(message, [])

            # Link enrich + actionable forms/docs/tools section
            text = enrich_answer_with_links(text, sources)
            try:
                from backend.services.actionable_content import attach_actionable_section

                text = attach_actionable_section(text, query=message, hits=None)
            except Exception as act_err:
                logger.debug("actionable content soft-fail: %s", act_err)
            # Final cleanup: never ship raw digest chrome
            text = re.sub(
                r"(?ms)\n*---\n*Live SBA API notes:.*$",
                "",
                text,
            ).rstrip()
            text = re.sub(r"(?m)^Source:\s*SBA API endpoint response\s*$", "", text)
            text = re.sub(r"(?m)^API route:\s*/api/sba/\S+\s*$", "", text)
            text = re.sub(r"(?m)^Retrieved children:.*$", "", text)
            text = re.sub(r"(?m)^Chunks:\s*\d+\s*$", "", text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
        except Exception as enrich_err:
            logger.warning("Chat link/KB enrich soft-fail: %s", enrich_err)
            try:
                from backend.services.link_enrichment import enrich_answer_with_links

                text = enrich_answer_with_links(text, sources)
            except Exception:
                pass

        # Format response for frontend
        response = {
            "success": result.get("success", True),
            "response": text,
            "message": text,
            "answer": text,
            "sources": sources,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "additional_data": result.get("additional_data", {}),
        }

        logger.info(
            f"Processed message for session {session_id}: {len(message)} chars -> {len(response['response'])} chars response"
        )
        return response

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")

        # Fallback response with navigable links
        try:
            from backend.services.link_enrichment import enrich_answer_with_links

            fallback = enrich_answer_with_links(
                "I apologize, but I'm experiencing technical difficulties. "
                "You can still open SBA resources using the links below.",
                [],
            )
        except Exception:
            fallback = (
                "I apologize, but I'm experiencing technical difficulties.\n\n"
                "## Links\n"
                "- [SBA Programs (in app)](/sba)\n"
                "- [Browse SBA Loans (in app)](/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans&t=SBA%20Loans)\n"
                "- [SBA Loans (official)](https://www.sba.gov/funding-programs/loans)"
            )
        return {
            "success": False,
            "response": fallback,
            "message": fallback,
            "answer": fallback,
            "sources": [],
            "session_id": session_id or str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }

def get_conversation_history(session_id):
    """
    Get conversation history for a session
    
    Args:
        session_id: Session identifier
    
    Returns:
        list: Conversation messages with metadata
    """
    try:
        concierge = get_concierge()
        
        if session_id in concierge.conversation_store:
            conversation = concierge.conversation_store[session_id]
            return conversation.get("messages", [])
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return []

def clear_conversation(session_id):
    """
    Clear conversation history for a session
    
    Args:
        session_id: Session identifier
    
    Returns:
        bool: Success status
    """
    try:
        concierge = get_concierge()
        
        if session_id in concierge.conversation_store:
            del concierge.conversation_store[session_id]
            logger.info(f"Cleared conversation for session: {session_id}")
            return True
        else:
            logger.warning(f"Session not found for clearing: {session_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return False
