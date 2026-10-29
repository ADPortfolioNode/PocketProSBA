import os
import logging
import time
import json
import re
import uuid
from datetime import datetime

from .base import BaseAssistant

# Configure logging
logger = logging.getLogger(__name__)

# Concierge behaviour rules (user-directed, 2026-10-25):
# - Expectation management: never present guidance as a loan approval,
#   eligibility decision, or legal/financial advice. A lender and the SBA
#   decide eligibility, amount, and timing, and will ask for documentation.
# - Limitation awareness: say plainly when vector retrieval (Chroma) or
#   another service is unavailable, instead of implying a full search ran.
# - An information request is a task: conversational answer first, then
#   SBA resources and next steps to complete it, with liability noted.
EXPECTATION_NOTE = (
    "\n\nExpectation note: This is SBA guidance only, not a loan approval, "
    "eligibility decision, or legal or financial advice. A lender and the SBA "
    "decide eligibility, amount, and timing, and will ask for documentation. "
    "Check the official SBA page in Resources before acting."
)
LIMITATION_RAG_NOTE = (
    "\n\nLimitation: Vector document retrieval is unavailable right now, so "
    "this answer is not from vector search. Use the live SBA resources in "
    "Resources to verify the current program details."
)
_FUNDING_WORDS = ("loan", "funding", "financing", "eligibility", "grant")

# Short, honest answer for questions about the assistant itself. A meta
# question ("what are your instructions?") must never be answered with a
# confident-looking SBA document dump — there is no instruction document to
# search, and pretending otherwise is exactly the overconfident tone to avoid.
META_ANSWER = (
    "I'm the SBA assistant inside this app. I find SBA guidance, explain "
    "programs in plain words, and point you to the official resources in the "
    "Resources panel. I can also walk through Daily tasks, like booking a room. "
    "I don't decide loan eligibility, I don't have access to your loan "
    "application, and I don't have a set of instructions I can show you — "
    "I just answer from SBA resources. What would you like help with?"
)
_META_PATTERNS = (
    "your instructions",
    "what instructions",
    "what are your instructions",
    "how do you work",
    "how does this work",
    "what can you do",
    "who are you",
    "what are you",
    "your capabilities",
)


# Words that mark a question as about an SBA topic, not a person. SBA API
# endpoints return program content only — they hold no person records —
# so a "who is <name>" question must never be answered from them.
_SBA_TOPIC_WORDS = {
    "sba", "loan", "loans", "administrator", "program", "programs",
    "lender", "lenders", "business", "funding", "grant", "grants",
    "microloan", "microloans", "express", "eligibility",
}


def _person_name_from(message):
    """Return (display_name, name_tokens) for a "who is <name>" question.

    Returns None for anything else — including "who are you" (the
    assistant itself, handled by the meta path) and SBA-role questions
    such as "who is the SBA administrator", which SBA content can answer.
    """
    if not message:
        return None
    m = re.match(
        r"\s*who\s+(?:is|was|['\u2019]s)\s+(.+?)\s*[?.!]*\s*$",
        message.strip(),
        flags=re.I,
    )
    if not m:
        return None
    name = m.group(1).strip()
    if not name or name.lower() in ("you", "yourself"):
        return None
    tokens = [
        w
        for w in re.findall(r"[a-z0-9]+", name.lower())
        if len(w) >= 3 and w not in ("the", "a", "an", "of", "for")
    ]
    if not tokens:
        return None
    if any(t in _SBA_TOPIC_WORDS for t in tokens):
        return None
    return name, tokens


# Lazy-load Gemini RAG service only when required
def _load_gemini_rag_service():
    try:
        from backend.gemini_rag_service import gemini_rag_service
        logger.info("Gemini RAG service imported successfully")
        return gemini_rag_service
    except Exception as e:
        logger.warning(f"Failed to import Gemini RAG service: {e}")
        return None

# Import self-optimizing components
try:
    from backend.services.task_orchestrator import TaskOrchestrator, StepAssistant
    from backend.services.memory_repository import MemoryRepository
    from backend.services.step_strategies import (
        DocumentSearchStrategy, TaskDecompositionStrategy, AnalysisStrategy, ResponseGenerationStrategy,
        FastDocumentSearchStrategy, DetailedDocumentSearchStrategy, LLMAnalysisStrategy, TemplateResponseStrategy
    )
    OPTIMIZING_AVAILABLE = True
    logger.info("Self-optimizing components imported successfully")
except ImportError as e:
    logger.warning(f"Failed to import self-optimizing components: {str(e)}")
    OPTIMIZING_AVAILABLE = False

class Concierge(BaseAssistant):
    """
    Concierge Assistant
    
    Main orchestrator and entry point for all user interactions.
    Handles task decomposition, routing to specialized agents,
    and response aggregation.
    """
    
    def __init__(self):
        """Initialize the Concierge assistant"""
        super().__init__("Concierge")
        self.conversation_store = {}
        
        # Initialize RAG manager
        try:
            try:
                from backend.services.rag import get_rag_manager
            except ImportError:
                from services.rag import get_rag_manager
            self.rag_manager = get_rag_manager()
        except Exception as e:
            logger.error(f"Failed to initialize RAG manager: {str(e)}")
            self.rag_manager = None
    
    def handle_message(self, message, session_id=None, metadata=None):
        """Handle a message from the user with improved dialogue flow"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # Start processing
        self._update_status("processing", 10, "Processing your message...")
        
        # Get or create conversation context
        conversation = self._get_or_create_conversation(session_id)
        
        # Add user message to conversation
        conversation["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Classify the message intent with improved context awareness
        intent = self._classify_intent(message, conversation)
        logger.info(f"Message classified as: {intent}")
        
        # Update status based on intent
        self._update_status("processing", 30, f"Handling {intent} request...")
        
        # Process based on intent with improved dialogue flow
        try:
            # Person questions are answered from the user's own documents
            # only, before any SBA path runs. SBA API endpoints return
            # program content, not person records, so their results are
            # not an answer to "who is <name>" — and must not be shown as
            # one. If no uploaded document covers the person, say so
            # plainly instead of falling through to SBA documents.
            person = _person_name_from(message)
            if person:
                display_name, name_tokens = person
                uploaded = self._uploaded_document_answer(
                    message, require_words=name_tokens
                )
                if uploaded:
                    response = dict(uploaded)
                    response["person_answer"] = True
                else:
                    response = {
                        "text": (
                            f"I don't have information about {display_name} "
                            "in your uploaded documents, and SBA program "
                            "resources don't hold person records, so I won't "
                            "guess. If you upload a document that covers "
                            f"{display_name}, I can answer from it. I can "
                            "help with SBA loans, programs, and business "
                            "guidance in the meantime."
                        ),
                        "sources": [],
                        "person_answer": True,
                    }
            elif intent == "meta":
                response = {"text": META_ANSWER, "sources": []}
            elif intent == "document_search":
                response = self._handle_document_search(message, conversation)
            elif intent == "task_request":
                response = self._handle_task_decomposition(message, conversation)
            elif intent == "greeting":
                response = {
                    "text": "Hello! I'm your SBA assistant. I'm here to help you navigate Small Business Administration programs, loans, and resources. What can I help you with today?",
                    "sources": []
                }
            elif intent == "acknowledgment":
                response = {
                    "text": "You're very welcome! I'm glad I could help. Is there anything else you'd like to know about SBA programs or small business resources?",
                    "sources": []
                }
            elif intent == "follow_up_query":
                # Handle follow-up questions with context from previous messages
                response = self._handle_follow_up_query(message, conversation)
            else:
                response = self._generate_direct_response(message, conversation)

            # Concierge behaviour: an information request is a task.
            # Conversational response first, then resources and next steps,
            # with limitations and liability stated plainly — never implied
            # as an approval or a complete search when a service is down.
            response_text = response.get("text", "")
            # A person answer is already a direct answer from the user's
            # own documents — it must not gain an "SBA guidance" task lead
            # or a RAG limitation note that would misdescribe it.
            if not response.get("person_answer") and intent in ("document_search", "simple_query", "follow_up_query"):
                task_lead = (
                    f"Got it — I'll take that as a task: find SBA guidance on "
                    f"{message.strip()}, summarize it, and point you to the "
                    f"official resources and next steps.\n\n"
                )
                if not response_text.startswith("Got it"):
                    response_text = task_lead + response_text
                try:
                    rag_available = bool(
                        self.rag_manager and self.rag_manager.is_available()
                    )
                except Exception:
                    rag_available = False
                if not rag_available and "Limitation:" not in response_text:
                    response_text += LIMITATION_RAG_NOTE
            if not response.get("person_answer") and intent in ("document_search", "task_request", "simple_query"):
                lowered = response_text.lower()
                if any(w in lowered for w in _FUNDING_WORDS) and "Expectation note:" not in response_text:
                    response_text += EXPECTATION_NOTE
            response["text"] = response_text

            # Add assistant response to conversation
            conversation["messages"].append({
                "role": "assistant",
                "content": response.get("text", ""),
                "timestamp": datetime.now().isoformat(),
                "sources": response.get("sources", [])
            })
            
            # Update conversation last activity
            conversation["last_activity"] = datetime.now().isoformat()
            
            # Log successful interaction for monitoring dialogue quality
            self._log_dialogue_quality(session_id, message, response.get("text", ""), intent)
            
            # Success!
            return self.report_success(
                text=response.get("text", ""),
                sources=response.get("sources", []),
                additional_data=response.get("additional_data", {})
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Provide more natural fallback response to minimize regression
            fallback_texts = [
                "I apologize, but I encountered a technical issue. Could you please try rephrasing your question?",
                "I'm having trouble processing that request right now. Please try asking in a different way.",
                "It seems there's a temporary issue. Let's try that again - could you rephrase your question?"
            ]
            fallback_text = fallback_texts[hash(message) % len(fallback_texts)]
            return self.report_failure(fallback_text)
    
    def _get_or_create_conversation(self, session_id):
        """Get or create a conversation context for a session"""
        if session_id not in self.conversation_store:
            self.conversation_store[session_id] = {
                "session_id": session_id,
                "messages": [],
                "user_info": {},
                "conversation_state": "information_gathering",
                "last_activity": datetime.now().isoformat()
            }
        return self.conversation_store[session_id]
    
    def _classify_intent(self, message, conversation):
        """Classify the intent of a user message with improved natural language understanding"""
        # Handle None or empty messages gracefully
        if not message or not message.strip():
            return "simple_query"
            
        message_lower = message.lower().strip()

        # Questions about the assistant itself win over every other pattern:
        # "what can you do" contains "do" (a task word) and "how do you work"
        # contains "how do i"-style phrasing, but neither is an SBA question.
        if any(p in message_lower for p in _META_PATTERNS):
            return "meta"

        # Strong task phrases win over an embedded search word such as
        # "research" in "Help me create a business plan ... research SBA
        # loan options". Without this, a multi-intent task request was
        # misclassified as a plain document search.
        strong_task_phrases = [
            "help me create", "help me build", "help me develop",
            "help me make", "create a business plan",
            "create a marketing strategy",
        ]
        if any(phrase in message_lower for phrase in strong_task_phrases):
            return "task_request"

        # Enhanced intent classification with better pattern matching
        # Document search intent
        search_patterns = [
            "find", "search", "look for", "any documents", "document", "file", 
            "information about", "details on", "what is", "tell me about",
            "how to get", "where can i find", "show me", "locate"
        ]
        
        # Task request intent
        task_patterns = [
            "help me", "create", "build", "develop", "make", "do", "assist with",
            "guide me", "walk me through", "step by step", "process for",
            "how do i", "what's the process", "need help with", "want to"
        ]
        
        # Check for document search intent with better context awareness
        if any(pattern in message_lower for pattern in search_patterns):
            # Additional context: if previous messages were about documents, maintain context
            if self._is_follow_up_search(conversation, message_lower):
                return "document_search"
            return "document_search"
        
        # Check for task request intent
        elif any(pattern in message_lower for pattern in task_patterns):
            # Check if this is a continuation of a previous task
            if self._is_task_continuation(conversation, message_lower):
                return "task_request"
            return "task_request"
        
        # Check for greetings and small talk
        elif any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return "greeting"
            
        # Check for thanks and acknowledgments
        elif any(thanks in message_lower for thanks in ["thank", "thanks", "appreciate", "grateful"]):
            return "acknowledgment"
            
        # Default to simple query for everything else
        else:
            # Check if this is a follow-up to previous conversation
            if self._is_follow_up_query(conversation, message_lower):
                return "follow_up_query"
            return "simple_query"
    
    def _is_follow_up_search(self, conversation, current_message):
        """Check if this is a follow-up to a previous search"""
        messages = conversation.get("messages", [])
        if len(messages) < 2:
            return False
            
        # Check if previous assistant message was about search results
        last_assistant_msg = next((msg for msg in reversed(messages) if msg.get("role") == "assistant"), None)
        if last_assistant_msg and any(term in last_assistant_msg.get("content", "").lower() for term in ["found", "search", "document", "result"]):
            return any(term in current_message for term in ["more", "another", "different", "other", "also"])
        return False
    
    def _is_task_continuation(self, conversation, current_message):
        """Check if this is a continuation of a previous task"""
        messages = conversation.get("messages", [])
        if len(messages) < 2:
            return False
            
        # Check if we were previously discussing a task
        last_assistant_msg = next((msg for msg in reversed(messages) if msg.get("role") == "assistant"), None)
        if last_assistant_msg and any(term in last_assistant_msg.get("content", "").lower() for term in ["task", "step", "process", "guide"]):
            return any(term in current_message for term in ["next", "then", "after", "continue", "proceed"])
        return False
    
    def _is_follow_up_query(self, conversation, current_message):
        """Check if this is a follow-up to previous conversation"""
        messages = conversation.get("messages", [])
        if len(messages) < 2:
            return False
            
        # Simple check: if the message is short and seems like a follow-up
        if len(current_message.split()) <= 4:
            return any(term in current_message for term in ["that", "it", "what", "how", "why", "when", "more", "next", "another", "also", "further", "continue"])
        return False
    
    def _handle_follow_up_query(self, message, conversation):
        """Handle follow-up questions with context from previous conversation"""
        messages = conversation.get("messages", [])
        
        # Look for the last assistant message to understand context
        last_assistant_msg = next((msg for msg in reversed(messages) if msg.get("role") == "assistant"), None)
        
        if last_assistant_msg:
            assistant_content = last_assistant_msg.get("content", "").lower()
            
            # Provide context-aware follow-up responses
            if any(term in assistant_content for term in ["loan", "funding", "financing"]):
                return {
                    "text": "Regarding the loan information I provided, would you like me to search for more specific details about application requirements, eligibility criteria, or different loan programs?",
                    "sources": []
                }
            elif any(term in assistant_content for term in ["business plan", "planning"]):
                return {
                    "text": "About the business planning resources, I can help you find templates, guides, or specific sections like market analysis or financial projections. What particular aspect would you like to explore further?",
                    "sources": []
                }
            elif any(term in assistant_content for term in ["grant", "funding"]):
                return {
                    "text": "Following up on the funding discussion, would you like me to search for information on specific grant opportunities, alternative funding sources, or eligibility requirements for different programs?",
                    "sources": []
                }
        
        # Generic follow-up response
        return {
            "text": "I'd be happy to provide more details about our previous discussion. Could you clarify what specific aspect you'd like me to expand on or search for more information about?",
            "sources": []
        }
    
    def _log_dialogue_quality(self, session_id, user_message, assistant_response, intent):
        """Log dialogue interactions for quality monitoring and regression detection"""
        try:
            dialogue_metrics = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "user_message_length": len(user_message),
                "assistant_response_length": len(assistant_response),
                "intent": intent,
                "response_quality": self._assess_response_quality(user_message, assistant_response),
                "has_sources": len(assistant_response) > 0  # Simplified check
            }
            
            logger.info(f"Dialogue quality metrics: {dialogue_metrics}")
            
        except Exception as e:
            logger.warning(f"Failed to log dialogue quality: {str(e)}")
    
    def _assess_response_quality(self, user_message, assistant_response):
        """Simple assessment of response quality to detect regression"""
        user_lower = user_message.lower()
        response_lower = assistant_response.lower()
        
        # Check for repetitive or generic responses
        generic_phrases = [
            "i understand you're asking about",
            "as an sba assistant",
            "could you provide more details",
            "what specific information"
        ]
        
        if any(phrase in response_lower for phrase in generic_phrases):
            return "generic"
        
        # Check if response addresses the user's question
        question_terms = ["what", "how", "why", "when", "where", "which"]
        if any(term in user_lower for term in question_terms) and "?" in user_message:
            if not any(term in response_lower for term in ["answer", "explain", "information", "detail"]):
                return "possibly_missing_answer"
        
        return "good"
    
    # --- Your own uploaded documents, before SBA content ----------------
    # Previously a document question fell through to the SBA knowledge base
    # first, so the concierge answered from SBA pages instead of the file
    # the user actually uploaded — and for PDF/DOCX uploads the file's text
    # was never extracted at all. Now the user's own documents are checked
    # first (RAG chunks, with a direct-file fallback when RAG is down), and
    # only if nothing of theirs matches does the SBA path run. This is what
    # makes chat + documents work as one app instead of two silos.
    def _uploaded_document_answer(self, message, require_words=None):
        """Answer from the user's uploaded documents, or None if no match.

        require_words (e.g. a person's full name tokens) narrows the match:
        only a document containing EVERY required word counts. Without it,
        the previous scoring applies (two distinctive words, or one word
        when the user is clearly asking about their own file).

        The RAG check reads a wide result set on purpose: a top-6 query can
        be crowded out by SBA documents, so an uploaded file that answers
        the question must not lose to program content it never competed
        with — local uploads and remote SBA results are both checked.
        """
        stopwords = {
            "what", "does", "says", "about", "tell", "show", "find", "search",
            "look", "from", "file", "document", "uploaded", "upload", "please",
            "there", "that", "this", "with", "your", "says",
        }
        words = [w for w in re.findall(r"[a-z0-9]+", message.lower()) if len(w) >= 4 and w not in stopwords]
        if not words:
            return None
        lower_msg = message.lower()

        def _score(text):
            hay = (text or "").lower()
            return sum(1 for w in words if w in hay)

        def _build(filename, text):
            excerpt = " ".join((text or "").split())[:900]
            return {
                "text": (
                    f"From your uploaded document **{filename}**:\n\n{excerpt}\n\n"
                    "Open Documents to see the full file."
                ),
                "sources": [{"title": filename, "path": "/documents", "url": "/documents"}],
            }

        # 1) RAG chunks (filename metadata marks a user upload)
        try:
            if self.rag_manager:
                results = self.rag_manager.query_documents(message, n_results=20)
                documents = results.get("documents") if isinstance(results, dict) else None
                metadatas = results.get("metadatas") if isinstance(results, dict) else None
                if documents and isinstance(documents[0], list):
                    documents = documents[0]
                if metadatas and isinstance(metadatas[0], list):
                    metadatas = metadatas[0]
                if documents and metadatas:
                    best = None
                    for doc, meta in zip(documents, metadatas):
                        meta = meta or {}
                        filename = meta.get("filename")
                        if not filename:
                            continue
                        if require_words and not all(
                            w in (doc or "").lower() for w in require_words
                        ):
                            continue
                        score = _score(doc)
                        name_hit = filename.lower() in lower_msg
                        # One distinctive word is enough when the user is
                        # clearly asking about their own file ("my lease",
                        # "my document"); two words are enough on their own.
                        mine = any(w in lower_msg for w in ("my ", "my\u2019", "uploaded", "document", "file"))
                        if name_hit or score >= 2 or (score >= 1 and mine):
                            if best is None or score > best[0]:
                                best = (score, filename, doc)
                    if best:
                        return _build(best[1], best[2])
        except Exception as rag_err:
            logger.debug("uploaded-document RAG check soft-fail: %s", rag_err)

        # 2) Direct file fallback (works even when Chroma is down)
        try:
            from backend.routes.files import _read_text
            from backend.routes import files as files_routes
            folder = getattr(files_routes, "UPLOAD_FOLDER", "uploads")
            if os.path.isdir(folder):
                best = None
                for filename in sorted(os.listdir(folder)):
                    filepath = os.path.join(folder, filename)
                    if not os.path.isfile(filepath):
                        continue
                    text = _read_text(filepath, filename)
                    if not text.strip():
                        continue
                    if require_words and not all(
                        w in text.lower() for w in require_words
                    ):
                        continue
                    score = _score(text)
                    name_hit = filename.lower() in lower_msg
                    mine = any(w in lower_msg for w in ("my ", "my\u2019", "uploaded", "document", "file"))
                    if name_hit or score >= 2 or (score >= 1 and mine):
                        if best is None or score > best[0]:
                            best = (score, filename, text)
                if best:
                    return _build(best[1], best[2])
        except Exception as file_err:
            logger.debug("uploaded-document file check soft-fail: %s", file_err)
        return None

    def _handle_document_search(self, message, conversation):
        """Handle a document search request — human-readable answer + clickable links."""
        self._update_status("searching", 50, "Searching for relevant documents...")

        # Daily operations workflows first: a question about booking a room,
        # a recording session, or a repair intake is answered from the Daily
        # task cards, not from SBA loan documents. This also seeds the
        # conversation — follow-ups can build on the task answer just given.
        # Generic only, no client branding, and demo-only limits are stated.
        try:
            from backend.services.daily_rag_ingest import search_daily_workflows

            daily = search_daily_workflows(message, max_results=2)
            if daily and daily[0].get("score", 0) >= 3:
                parts = [
                    "Here is how that Daily task works:\n",
                ]
                sources = []
                for hit in daily:
                    parts.append(f"**{hit['title']}**\n{hit['body']}\n")
                    sources.append(
                        {"title": hit["title"], "path": "/daily", "url": "/daily"}
                    )
                parts.append(
                    "\nDemo only: Daily workflows take no payments and make no real "
                    "reservations. Open Daily to try the task, and verify rates and "
                    "policies with the business before booking."
                )
                return {"text": "\n".join(parts), "sources": sources}
        except Exception as daily_err:
            logger.debug("daily workflows search soft-fail: %s", daily_err)

        # Your own files are checked now, but NOT returned on their own:
        # the conversation leads with the SBA answer, and a matching file
        # is added afterwards as supporting bonus material, with its link
        # in the Resources panel (sources), never as a link list in the bubble.
        uploaded = self._uploaded_document_answer(message)

        # Live SBA API digests (parent→child explore) when keyword match is strong
        sba_text = None
        sba_sources = []
        try:
            from backend.routes.rag import _local_kb_sba_answer
            from backend.services.link_enrichment import enrich_answer_with_links

            kb = _local_kb_sba_answer(message, max_chunks=6)
            if isinstance(kb, dict) and kb.get("mode") == "sba_api_live" and kb.get("answer"):
                from pathlib import Path
                from backend.services.chat_answer_format import (
                    format_hits_as_answer,
                    normalize_hits,
                )

                sources = kb.get("source_documents") or kb.get("sources") or []
                full_docs = []
                full_meta = []
                for s in sources:
                    if not isinstance(s, dict):
                        continue
                    meta = s.get("metadata") or {}
                    path = str(meta.get("path") or "")
                    body = s.get("content") or s.get("snippet") or ""
                    # Prefer full live digest file (not tiny snippet)
                    if path.endswith(".txt"):
                        try:
                            p = Path(path)
                            if p.exists() and "manifest" not in p.name:
                                body = p.read_text(encoding="utf-8", errors="replace")
                        except Exception:
                            pass
                    if "manifest" in path:
                        continue
                    # Infer title/route from filename api_sba_content_loans_7a__overview.txt
                    title = meta.get("title") or ""
                    route = ""
                    name = path.replace("\\", "/").rsplit("/", 1)[-1]
                    m = re.match(r"api_sba_(.+?)__(?:combined|overview|child_[^.]+)\.txt$", name)
                    if m:
                        slug = m.group(1)
                        if slug.startswith("content_"):
                            rest = slug[len("content_") :]
                            parts = rest.split("_")
                            if parts:
                                route = f"/api/sba/content/{parts[0]}"
                                if len(parts) > 1:
                                    route += "/" + "/".join(parts[1:])
                        title = title or route.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").title()
                    full_docs.append(body)
                    full_meta.append(
                        {
                            "source": "sba_api",
                            "title": title,
                            "route": route,
                            "path": route or path,
                            "url": "",
                        }
                    )
                hits = normalize_hits(full_docs, full_meta)
                if hits:
                    sba_text, sba_sources = format_hits_as_answer(message, hits)
                # Last resort: cleaned text + links (never raw Source N: sba_api)
                text = re.sub(
                    r"^Based on (live SBA API digests|the local SBA knowledge base)[^\n]*\n+",
                    "",
                    kb.get("answer") or "",
                    flags=re.I,
                )
                sba_text = enrich_answer_with_links(
                    f"Here’s a clear summary from live SBA resources about **{message.strip()}**:\n\n{text}",
                    sources,
                )
                sba_sources = list(sources)
        except Exception as kb_err:
            logger.debug("local KB path soft-fail in document search: %s", kb_err)

        # Combine: conversation first (SBA), supporting files as a bonus.
        # Any link list the enrich fallback appended is stripped — those
        # links live in the Resources panel via sources, not in the bubble.
        if sba_text:
            sba_text = re.sub(r"\n##\s*Links\b.*$", "", sba_text, flags=re.S)
            sba_text = re.sub(r"\n###\s*More links\b.*$", "", sba_text, flags=re.S)
            sba_text = sba_text.rstrip()
            if uploaded:
                combined = (
                    f"{sba_text}\n\n"
                    "As a bonus, your own files also cover this:\n\n"
                    f"{uploaded['text']}"
                )
                return {
                    "text": combined,
                    "sources": list(sba_sources) + list(uploaded.get("sources") or []),
                }
            return {"text": sba_text, "sources": sba_sources}
        if uploaded:
            return uploaded

        if not self.rag_manager:
            try:
                from backend.services.link_enrichment import enrich_answer_with_links
                return {
                    "text": enrich_answer_with_links(
                        "Document search is limited right now. Use the links below to open live SBA resources.",
                        [],
                    ),
                    "sources": [],
                }
            except Exception:
                return {
                    "text": "I'm sorry, but the document search functionality is not available at the moment.",
                    "sources": [],
                }

        # Perform search
        results = self.rag_manager.query_documents(message, n_results=6)

        if "error" in results:
            return {
                "text": (
                    f"I encountered an error while searching: {results['error']}."
                    + LIMITATION_RAG_NOTE
                ),
                "sources": [],
            }

        try:
            from backend.services.chat_answer_format import format_chroma_query_result

            formatted = format_chroma_query_result(message, results)
            if formatted:
                return formatted
        except Exception as fmt_err:
            logger.warning("chat answer format soft-fail: %s", fmt_err)

        return {
            "text": "I couldn't find any relevant documents matching your query. Try browsing SBA Loans in the app.",
            "sources": [],
        }
    
    def _handle_task_decomposition(self, message, conversation):
        """Handle a complex task request using Gemini LM instead of templates"""
        self._update_status("planning", 40, "Analyzing your request...")

        # Use Gemini RAG service for natural language responses
        gemini_rag_service = _load_gemini_rag_service()
        if gemini_rag_service:
            try:
                # Query the Gemini RAG service for task-related information
                result = gemini_rag_service.query_sba_loans(message)

                if "error" not in result:
                    return {
                        "text": result.get("answer", "I can help you with that task. Let me search for relevant SBA resources and information."),
                        "sources": result.get("source_documents", [])
                    }
            except Exception as e:
                logger.warning(f"Gemini RAG query failed for task decomposition: {str(e)}")

        # Fallback to RAG manager if Gemini is not available
        if self.rag_manager:
            try:
                results = self.rag_manager.query_documents(message, n_results=3)

                if "error" not in results:
                    try:
                        from backend.services.chat_answer_format import format_chroma_query_result

                        formatted = format_chroma_query_result(message, results)
                        if formatted:
                            # Task-oriented lead-in
                            formatted["text"] = (
                                "Here’s how SBA resources can help with that:\n\n"
                                + formatted["text"]
                            )
                            return formatted
                    except Exception as e:
                        logger.warning("task RAG format soft-fail: %s", e)
            except Exception as e:
                logger.warning(f"RAG manager query failed for task decomposition: {str(e)}")

        # Final fallback - generic response without templates
        return {
            "text": f"I understand you need help with '{message}'. Let me search through SBA resources to provide you with the most relevant information and guidance for your specific situation. What particular aspect would you like me to focus on?",
            "sources": []
        }
    
    def _generate_direct_response(self, message, conversation):
        """Generate a direct response to a simple query with improved natural language"""
        self._update_status("thinking", 60, "Generating a helpful response...")
        
        # Handle None or empty messages gracefully
        if not message or not message.strip():
            message = "your question"
            return {
                "text": "I'm here to help! What would you like to know about SBA programs, loans, or small business resources?",
                "sources": []
            }
        
        message_lower = message.lower().strip()
        
        # Handle greetings naturally
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            return {
                "text": "Hello! I'm your SBA assistant. I'm here to help you navigate Small Business Administration programs, loans, and resources. What can I help you with today?",
                "sources": []
            }
        
        # Handle thanks and acknowledgments
        if any(thanks in message_lower for thanks in ["thank", "thanks", "appreciate", "grateful"]):
            return {
                "text": "You're very welcome! I'm glad I could help. Is there anything else you'd like to know about SBA programs or small business resources?",
                "sources": []
            }
        
        # Handle follow-up questions with context awareness
        messages = conversation.get("messages", [])
        if len(messages) > 1 and self._is_follow_up_query(conversation, message_lower):
            last_assistant_msg = next((msg for msg in reversed(messages) if msg.get("role") == "assistant"), None)
            if last_assistant_msg:
                return {
                    "text": f"Regarding your previous question, I'd be happy to provide more details. Could you clarify what specific aspect you'd like me to expand on?",
                    "sources": []
                }
        
        if self.rag_manager:
            try:
                # Use RAG to generate a response (human-readable + clickable links)
                results = self.rag_manager.query_documents(message, n_results=6)

                if "error" not in results:
                    try:
                        from backend.services.chat_answer_format import format_chroma_query_result
                        from backend.services.link_enrichment import enrich_answer_with_links

                        formatted = format_chroma_query_result(message, results)
                        if formatted:
                            return formatted
                        if results.get("answer"):
                            return {
                                "text": enrich_answer_with_links(
                                    results.get("answer", ""),
                                    results.get("source_documents") or [],
                                ),
                                "sources": results.get("source_documents") or [],
                            }
                    except Exception as e:
                        logger.warning("RAG format soft-fail: %s", e)
            except Exception as e:
                logger.warning(f"RAG query failed, falling back to direct response: {str(e)}")
                # Continue to fallback response
        
        # Fallback to direct response without RAG - more natural and varied
        fallback_responses = [
            f"I'd be happy to help you with {message.strip()}. The SBA offers various resources that might be relevant. Could you tell me a bit more about what specific information you're looking for?",
            f"That's a great question about {message.strip()}! The Small Business Administration has programs and resources that could help. What aspect of this are you most interested in learning about?",
            f"I understand you're asking about {message.strip()}. As an SBA assistant, I can help you explore loan options, business planning resources, and program eligibility. Would you like me to search for specific information on this topic?",
            f"Thanks for your question about {message.strip()}. The SBA provides comprehensive support for small businesses. I can help you find information about relevant programs and resources. What specific area would you like to focus on?"
        ]
        
        # Use conversation context to choose appropriate response
        response_index = hash(message) % len(fallback_responses)
        response_text = fallback_responses[response_index]
        
        return {
            "text": response_text,
            "sources": []
        }
