import os
import logging
import time
import json
import uuid
from datetime import datetime

from .base import BaseAssistant

# Configure logging
logger = logging.getLogger(__name__)

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
        """Handle a message from the user"""
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
        
        # Classify the message intent
        intent = self._classify_intent(message, conversation)
        logger.info(f"Message classified as: {intent}")
        
        # Update status based on intent
        self._update_status("processing", 30, f"Handling {intent} request...")
        
        # Process based on intent
        try:
            if intent == "document_search":
                response = self._handle_document_search(message, conversation)
            elif intent == "task_request":
                response = self._handle_task_decomposition(message, conversation)
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
            
            # Success!
            return self.report_success(
                text=response.get("text", ""),
                sources=response.get("sources", []),
                additional_data=response.get("additional_data", {})
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Provide fallback response to minimize regression
            fallback_text = "Sorry, I encountered an error but I'm here to help. Please try rephrasing your request."
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
        """Classify the intent of a user message"""
        # Handle None or empty messages gracefully
        if not message:
            return "simple_query"
            
        # Simple keyword-based classification for now
        message_lower = message.lower()
        
        if any(term in message_lower for term in ["find", "search", "look for", "any documents"]):
            return "document_search"
        elif any(term in message_lower for term in ["help me", "create", "build", "develop", "make", "do"]):
            return "task_request"
        else:
            return "simple_query"
    
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
        """Handle a complex task request by decomposing it into steps"""
        self._update_status("planning", 40, "Breaking down your request into steps...")
        
        # For now, return a simple response
        return {
            "text": "I understand you want me to help with a complex task. Currently, I'm not fully equipped to handle complex task decomposition, but I can provide information about small business resources and SBA programs.",
            "sources": []
        }
    
    def _generate_direct_response(self, message, conversation):
        """Generate a direct response to a simple query"""
        self._update_status("thinking", 60, "Generating a response...")
        
        # Handle None or empty messages gracefully
        if not message:
            message = "your question"
        
        if self.rag_manager:
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
                
                # Generate response
                response_text = f"Based on the information I have, {message.strip()}\n\n"
                response_text += f"Here's what I know: {context}"
                
                return {
                    "text": response_text,
                    "sources": sources
                }
        
        # Fallback to direct response without RAG
        response_text = f"I understand you're asking about {message.strip()}. As an SBA assistant, I can help with small business questions, loan information, and business planning resources. Could you provide more details about what specific information you're looking for?"
        
        return {
            "text": response_text,
            "sources": []
        }
