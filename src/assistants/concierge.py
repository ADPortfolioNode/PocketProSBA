"""
Concierge Assistant - Main orchestrator and entry point for user interactions.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from src.assistants.base_assistant import BaseAssistant
from src.services.chroma_service import get_chroma_service_instance
from src.services.rag_manager import get_rag_manager
from src.services.llm_factory import LLMFactory
from src.services.conversation_store import get_conversation_store, get_current_session_id
from src.services.model_discovery import ModelDiscoveryService


class Concierge(BaseAssistant):
    """Main orchestrator assistant for user interactions."""
    
    def __init__(self):
        super().__init__("Concierge")
        self.chroma_service = get_chroma_service_instance()
        self.rag_manager = get_rag_manager()
        self.llm = LLMFactory.get_llm()
        self.conversation_store = get_conversation_store()
        self.model_discovery = ModelDiscoveryService()
        
        # System prompt for the Concierge
        self.system_prompt = """You are the PocketPro:SBA Edition Concierge, an expert assistant that helps users find information and complete tasks. 
        You have access to a document repository and can search for relevant information.
        You are helpful, professional, and focused on providing accurate information from available sources.
        If you cannot find relevant information in the documents, say so clearly and offer to help in other ways."""

    def get_system_greeting(self) -> Dict[str, Any]:
        """Generate a greeting message with system status when app is ready."""
        try:
            # Get system status
            status_info = self.get_system_status()
            
            # Generate personalized greeting
            current_time = datetime.now()
            hour = current_time.hour
            
            if hour < 12:
                time_greeting = "Good morning"
            elif hour < 17:
                time_greeting = "Good afternoon"
            else:
                time_greeting = "Good evening"
            
            greeting_parts = [
                f"👋 {time_greeting}! Welcome to **PocketPro:SBA Edition**.",
                "",
                "🚀 **System Status**: All systems operational and ready to assist you!",
                "",
                f"🤖 **AI Model**: {status_info['current_model']} ({status_info['llm_status']})",
                f"📚 **Document Database**: {status_info['document_count']} documents indexed",
                f"🔍 **Vector Search**: {status_info['chroma_status']}",
                "",
                "**What I can help you with:**",
                "• 📄 Search and analyze your uploaded documents",
                "• 🎯 Break down complex tasks into manageable steps", 
                "• 💡 Answer questions using your knowledge base",
                "• 📊 Provide insights from your document collection",
                "",
                "**Quick Tips:**",
                "• Upload documents using the file upload feature",
                "• Ask me questions about your documents",
                "• Request task breakdowns for complex projects",
                "",
                "How can I assist you today? 😊"
            ]
            
            greeting_text = "\n".join(greeting_parts)
            
            return self.report_success(
                text=greeting_text,
                additional_data={
                    "greeting": True,
                    "system_status": status_info,
                    "timestamp": current_time.isoformat()
                }
            )
            
        except Exception as e:
            return self.report_success(
                text="👋 Welcome to PocketPro:SBA Edition! I'm your AI assistant, ready to help you with document analysis and task management. How can I assist you today?",
                additional_data={
                    "greeting": True,
                    "error": str(e)
                }
            )

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status information."""
        try:
            # Get model information
            available_models = self.model_discovery.get_available_models()
            current_model = getattr(self.llm, 'model_name', 'Unknown')
            
            # Get LLM status
            try:
                # Test LLM with a simple query
                test_response = self.llm.generate_response("Test", "", "Respond with 'OK'")
                llm_status = "Connected" if test_response else "Disconnected"
            except:
                llm_status = "Disconnected"
            
            # Get ChromaDB status
            collection_stats = self.chroma_service.get_collection_stats()
            chroma_status = "Connected" if collection_stats.get("success", False) else "Disconnected"
            document_count = collection_stats.get("document_count", 0)
            
            return {
                "current_model": current_model,
                "available_models_count": len(available_models),
                "llm_status": llm_status,
                "chroma_status": chroma_status,
                "document_count": document_count,
                "system_ready": llm_status == "Connected"
            }
            
        except Exception as e:
            return {
                "current_model": "Unknown",
                "available_models_count": 0,
                "llm_status": "Error",
                "chroma_status": "Error", 
                "document_count": 0,
                "system_ready": False,
                "error": str(e)
            }

    def handle_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle incoming message and coordinate response."""
        try:
            # Check for greeting request
            if message.lower().strip() in ["hello", "hi", "hey", "start", "greeting", "status"]:
                return self.get_system_greeting()
            
            self._update_status("processing", 10, "Processing user message...")
            
            # Get conversation context
            session_id = get_current_session_id()
            conversation = self.conversation_store.get_conversation(session_id)
            
            # Add user message to conversation
            conversation.add_message("user", message)
            
            self._update_status("processing", 30, "Analyzing message intent...")
            
            # Classify the message intent
            intent = self._classify_intent(message, conversation)
            
            # Process based on intent
            if intent == "document_search":
                self._update_status("processing", 50, "Searching documents...")
                response = self._handle_document_search(message, conversation)
            elif intent == "task_request":
                self._update_status("processing", 50, "Processing task request...")
                response = self._handle_task_decomposition(message, conversation)
            else:
                self._update_status("processing", 50, "Generating response...")
                response = self._generate_direct_response(message, conversation)
            
            # Add assistant response to conversation
            conversation.add_message("assistant", response.get("text", ""))
            
            return response
            
        except Exception as e:
            print(f"Error in Concierge.handle_message: {e}")
            return self.report_failure(f"I encountered an error while processing your message: {str(e)}")
    
    def _classify_intent(self, message: str, conversation) -> str:
        """Classify user message intent."""
        try:
            # Get conversation context
            context_string = conversation.get_context_string(6)
            
            # Use LLM to classify intent
            intent = self.llm.classify_intent(message, context_string)
            
            # Validate intent
            valid_intents = ["simple_query", "document_search", "task_request", "clarification", "feedback", "meta"]
            if intent not in valid_intents:
                intent = "simple_query"  # Default fallback
            
            return intent
            
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "simple_query"
    
    def _handle_document_search(self, message: str, conversation) -> Dict[str, Any]:
        """Handle document search requests."""
        try:
            # Use RAG to get response with sources
            rag_response = self.rag_manager.generate_rag_response(
                query=message,
                system_prompt=self.system_prompt
            )
            
            if rag_response.get("success", False):
                return self.report_success(
                    text=rag_response["text"],
                    additional_data={
                        "sources": rag_response.get("sources", []),
                        "context_used": rag_response.get("context_used", False)
                    }
                )
            else:
                return self.report_failure("I couldn't retrieve relevant information at this time.")
                
        except Exception as e:
            return self.report_failure(f"Error during document search: {str(e)}")
    
    def _handle_task_decomposition(self, message: str, conversation) -> Dict[str, Any]:
        """Handle complex task requests that need decomposition."""
        try:
            # For now, delegate task requests to document search
            # In a full implementation, this would involve the Task Assistant
            self._update_status("processing", 70, "Delegating to search...")
            return self._handle_document_search(message, conversation)
            
        except Exception as e:
            return self.report_failure(f"Error processing task: {str(e)}")
    
    def _generate_direct_response(self, message: str, conversation) -> Dict[str, Any]:
        """Generate direct conversational response."""
        try:
            # Get conversation context
            context_string = conversation.get_context_string(6)
            
            # Check if we should search documents anyway
            collection_stats = self.rag_manager.get_collection_stats()
            if collection_stats.get("document_count", 0) > 0:
                # Try document search first for better responses
                search_response = self._handle_document_search(message, conversation)
                if search_response.get("success", False):
                    return search_response
            
            # Generate direct response
            response_text = self.llm.generate_response(
                prompt=message,
                context=context_string,
                system_prompt=self.system_prompt
            )
            
            return self.report_success(
                text=response_text,
                additional_data={
                    "sources": [],
                    "context_used": bool(context_string)
                }
            )
            
        except Exception as e:
            return self.report_failure(f"Error generating response: {str(e)}")


# Factory function for creating Concierge instances
def create_concierge() -> Concierge:
    """Create a new Concierge assistant instance."""
    return Concierge()
