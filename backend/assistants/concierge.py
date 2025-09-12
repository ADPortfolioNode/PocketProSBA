import os
import logging
import time
import json
import uuid
from datetime import datetime

from .base import BaseAssistant

# Configure logging
logger = logging.getLogger(__name__)

# Import Gemini RAG service
try:
    from backend.gemini_rag_service import gemini_rag_service
    GEMINI_AVAILABLE = True
    logger.info("✅ Gemini RAG service imported successfully")
except ImportError as e:
    logger.warning(f"❌ Failed to import Gemini RAG service: {str(e)}")
    GEMINI_AVAILABLE = False
    gemini_rag_service = None

# Import self-optimizing components
try:
    from services.task_orchestrator import TaskOrchestrator, StepAssistant
    from services.memory_repository import MemoryRepository
    from services.step_strategies import (
        DocumentSearchStrategy, TaskDecompositionStrategy, AnalysisStrategy, ResponseGenerationStrategy,
        FastDocumentSearchStrategy, DetailedDocumentSearchStrategy, LLMAnalysisStrategy, TemplateResponseStrategy
    )
    OPTIMIZING_AVAILABLE = True
    logger.info("✅ Self-optimizing components imported successfully")
except ImportError as e:
    logger.warning(f"❌ Failed to import self-optimizing components: {str(e)}")
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
            if intent == "document_search":
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
        if len(current_message.split()) <= 3:
            return any(term in current_message for term in ["that", "it", "what", "how", "why", "when"])
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
    
    def _handle_document_search(self, message, conversation):
        """Handle a document search request"""
        self._update_status("searching", 50, "Searching for relevant documents...")
        
        if not self.rag_manager:
            return {
                "text": "I'm sorry, but the document search functionality is not available at the moment.",
                "sources": []
            }
        
        # Perform search
        results = self.rag_manager.query_documents(message, n_results=3)
        
        if "error" in results:
            return {
                "text": f"I encountered an error while searching: {results['error']}",
                "sources": []
            }
        
        # Format results
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        if not documents:
            return {
                "text": "I couldn't find any relevant documents matching your query.",
                "sources": []
            }
        
        # Build response
        formatted_sources = []
        context = ""
        
        for i, (doc, meta, doc_id) in enumerate(zip(documents, metadatas, ids)):
            source_name = meta.get("source", f"Document {i+1}")
            formatted_sources.append({
                "id": doc_id,
                "name": source_name,
                "content": doc[:200] + "..." if len(doc) > 200 else doc,
                "metadata": meta
            })
            context += f"\nSource {i+1} ({source_name}): {doc}\n"
        
        # Generate response with context
        response_text = f"Here's what I found regarding your query:\n\n"
        
        for i, source in enumerate(formatted_sources):
            response_text += f"Source {i+1}: {source['name']}\n"
            response_text += f"{source['content']}\n\n"
        
        return {
            "text": response_text,
            "sources": formatted_sources
        }
    
    def _handle_task_decomposition(self, message, conversation):
        """Handle a complex task request using Gemini LM instead of templates"""
        self._update_status("planning", 40, "Analyzing your request...")

        # Use Gemini RAG service for natural language responses
        if GEMINI_AVAILABLE and gemini_rag_service:
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

                if "error" not in results and results.get("documents", [[]])[0]:
                    documents = results.get("documents", [[]])[0]
                    metadatas = results.get("metadatas", [[]])[0]
                    ids = results.get("ids", [[]])[0]

                    # Build context from retrieved documents
                    context = "\n".join(documents)

                    # Format sources
                    sources = []
                    for i, (doc, meta, doc_id) in enumerate(zip(documents, metadatas, ids)):
                        source_name = meta.get("source", f"Document {i+1}")
                        sources.append({
                            "id": doc_id,
                            "name": source_name,
                            "content": doc[:200] + "..." if len(doc) > 200 else doc,
                            "metadata": meta
                        })

                    # Generate response using context
                    response_text = f"Based on SBA resources, here's how I can help you with your task:\n\n{context}\n\nWould you like me to break this down into specific steps or provide more detailed information about any particular aspect?"

                    return {
                        "text": response_text,
                        "sources": sources
                    }
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
                # Use RAG to generate a response
                results = self.rag_manager.query_documents(message, n_results=2)
                
                if "error" not in results and results.get("answer"):
                    # Enhanced Gemini RAG service response format
                    answer = results.get("answer", "")
                    source_documents = results.get("source_documents", [])
                    
                    # Format sources
                    sources = []
                    for i, source in enumerate(source_documents):
                        source_name = source.get("metadata", {}).get("source", f"Document {i+1}")
                        sources.append({
                            "id": f"source_{i}",
                            "name": source_name,
                            "content": source.get("content", ""),
                            "metadata": source.get("metadata", {})
                        })
                    
                    return {
                        "text": answer,
                        "sources": sources
                    }
                elif "error" not in results and results.get("documents", [[]])[0]:
                    # Legacy RAG service response format (fallback)
                    documents = results.get("documents", [[]])[0]
                    metadatas = results.get("metadatas", [[]])[0]
                    ids = results.get("ids", [[]])[0]
                    
                    # Build context
                    context = "\n".join(documents)
                    
                    # Format sources
                    sources = []
                    for i, (doc, meta, doc_id) in enumerate(zip(documents, metadatas, ids)):
                        source_name = meta.get("source", f"Document {i+1}")
                        sources.append({
                            "id": doc_id,
                            "name": source_name,
                            "content": doc[:200] + "..." if len(doc) > 200 else doc,
                            "metadata": meta
                        })
                    
                    # Generate more natural response
                    response_text = f"Based on SBA resources, here's what I found about {message.strip()}:\n\n{context}"
                    
                    return {
                        "text": response_text,
                        "sources": sources
                    }
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
