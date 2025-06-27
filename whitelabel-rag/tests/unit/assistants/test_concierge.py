"""
Tests for the Concierge Agent
"""
import pytest
from unittest.mock import patch, MagicMock

try:
    from app.services.concierge import Concierge
except ImportError as e:
    pytest.skip(f"Could not import app.services.concierge: {e}")

class TestConcierge:
    """Tests for the Concierge agent"""
    
    def test_initialization(self):
        """Test basic initialization of Concierge."""
        with patch('app.services.concierge.get_chroma_service_instance') as mock_chroma:
            with patch('app.services.concierge.get_rag_manager') as mock_rag:
                with patch('app.services.concierge.LLMFactory') as mock_llm_factory:
                    with patch('app.services.concierge.ConversationStore') as mock_conv_store:
                        concierge = Concierge()
                        
                        assert concierge.name == "Concierge"
                        assert hasattr(concierge, "chroma_service")
                        assert hasattr(concierge, "rag_manager")
                        assert hasattr(concierge, "llm")
                        assert hasattr(concierge, "conversation_store")
    
    @patch('app.services.concierge.get_chroma_service_instance')
    @patch('app.services.concierge.get_rag_manager')
    @patch('app.services.concierge.LLMFactory')
    @patch('app.services.concierge.ConversationStore')
    @patch('app.services.concierge.get_current_session_id')
    def test_handle_message_simple_query(self, mock_session_id, mock_conv_store, mock_llm_factory, 
                                         mock_rag, mock_chroma):
        """Test handle_message with a simple query."""
        # Setup mocks
        mock_session_id.return_value = "test-session"
        mock_conversation = MagicMock()
        mock_conv_store_instance = MagicMock()
        mock_conv_store.return_value = mock_conv_store_instance
        mock_conv_store_instance.get_conversation.return_value = mock_conversation
        
        mock_llm = MagicMock()
        mock_llm_factory.get_llm.return_value = mock_llm
        mock_llm.generate_text.return_value = "This is a response to your query."
        
        # Create the concierge
        concierge = Concierge()
        
        # Mock the _classify_intent method to return a simple query
        with patch.object(concierge, '_classify_intent', return_value="simple_query"):
            # Mock the direct response method
            with patch.object(concierge, '_generate_direct_response') as mock_direct_response:
                mock_direct_response.return_value = {
                    "text": "This is a direct response.", 
                    "assistant": "Concierge"
                }
                
                # Test handle_message
                result = concierge.handle_message("What is the capital of France?")
                
                # Verify conversation was updated
                mock_conversation.add_message.assert_called_once_with("user", "What is the capital of France?")
                
                # Verify intent was classified
                concierge._classify_intent.assert_called_once()
                
                # Verify direct response was generated
                mock_direct_response.assert_called_once()
                
                # Verify result
                assert result["text"] == "This is a direct response."
                assert result["assistant"] == "Concierge"
    
    @patch('app.services.concierge.get_chroma_service_instance')
    @patch('app.services.concierge.get_rag_manager')
    @patch('app.services.concierge.LLMFactory')
    @patch('app.services.concierge.ConversationStore')
    @patch('app.services.concierge.get_current_session_id')
    def test_handle_document_search(self, mock_session_id, mock_conv_store, mock_llm_factory, 
                                   mock_rag, mock_chroma):
        """Test handle_message with a document search query."""
        # Setup mocks
        mock_session_id.return_value = "test-session"
        mock_conversation = MagicMock()
        mock_conv_store_instance = MagicMock()
        mock_conv_store.return_value = mock_conv_store_instance
        mock_conv_store_instance.get_conversation.return_value = mock_conversation
        
        # Create the concierge
        concierge = Concierge()
        
        # Mock the _classify_intent method to return document_search
        with patch.object(concierge, '_classify_intent', return_value="document_search"):
            # Mock the document search method
            with patch.object(concierge, '_handle_document_search') as mock_search:
                mock_search.return_value = {
                    "text": "I found these documents about climate change.", 
                    "assistant": "Concierge",
                    "sources": ["doc1.pdf", "doc2.pdf"]
                }
                
                # Test handle_message
                result = concierge.handle_message("Find information about climate change")
                
                # Verify conversation was updated
                mock_conversation.add_message.assert_called_once_with(
                    "user", "Find information about climate change"
                )
                
                # Verify intent was classified
                concierge._classify_intent.assert_called_once()
                
                # Verify document search was handled
                mock_search.assert_called_once()
                
                # Verify result
                assert result["text"] == "I found these documents about climate change."
                assert result["assistant"] == "Concierge"
                assert result["sources"] == ["doc1.pdf", "doc2.pdf"]
    
    @patch('app.services.concierge.get_chroma_service_instance')
    @patch('app.services.concierge.get_rag_manager')
    @patch('app.services.concierge.LLMFactory')
    @patch('app.services.concierge.ConversationStore')
    @patch('app.services.concierge.get_current_session_id')
    def test_handle_task_decomposition(self, mock_session_id, mock_conv_store, mock_llm_factory, 
                                      mock_rag, mock_chroma):
        """Test handle_message with a task request."""
        # Setup mocks
        mock_session_id.return_value = "test-session"
        mock_conversation = MagicMock()
        mock_conv_store_instance = MagicMock()
        mock_conv_store.return_value = mock_conv_store_instance
        mock_conv_store_instance.get_conversation.return_value = mock_conversation
        
        # Create the concierge
        concierge = Concierge()
        
        # Mock the _classify_intent method to return task_request
        with patch.object(concierge, '_classify_intent', return_value="task_request"):
            # Mock the task decomposition method
            with patch.object(concierge, '_handle_task_decomposition') as mock_task:
                mock_task.return_value = {
                    "text": "I'll help you book a flight. Here's my plan...", 
                    "assistant": "Concierge",
                    "task_id": "task-123"
                }
                
                # Test handle_message
                result = concierge.handle_message("Book a flight from NYC to London")
                
                # Verify conversation was updated
                mock_conversation.add_message.assert_called_once_with(
                    "user", "Book a flight from NYC to London"
                )
                
                # Verify intent was classified
                concierge._classify_intent.assert_called_once()
                
                # Verify task decomposition was handled
                mock_task.assert_called_once()
                
                # Verify result
                assert result["text"] == "I'll help you book a flight. Here's my plan..."
                assert result["assistant"] == "Concierge"
                assert result["task_id"] == "task-123"
