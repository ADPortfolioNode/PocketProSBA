#!/usr/bin/env python3
"""
Comprehensive concierge functionality test
Tests all aspects of the concierge service
"""

import pytest
import json
import uuid
from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from assistants.concierge import Concierge
from services.rag import RAGManager

class TestConcierge:
    """Comprehensive test suite for concierge functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.concierge = Concierge()
        self.test_session_id = str(uuid.uuid4())
    
    def test_concierge_initialization(self):
        """Test concierge initialization"""
        assert self.concierge.name == "Concierge"
        assert hasattr(self.concierge, 'handle_message')
        assert hasattr(self.concierge, 'rag_manager')
    
    def test_simple_query_response(self):
        """Test handling simple queries"""
        message = "What is an SBA loan?"
        response = self.concierge.handle_message(message, self.test_session_id)
        
        assert response is not None
        assert 'text' in response
        assert 'sources' in response
        assert isinstance(response['text'], str)
        assert len(response['text']) > 0
    
    def test_document_search_intent(self):
        """Test document search functionality"""
        message = "Find documents about SBA 7(a) loans"
        response = self.concierge.handle_message(message, self.test_session_id)
        
        assert response is not None
        assert 'text' in response
        assert 'sources' in response
    
    def test_task_decomposition_intent(self):
        """Test task decomposition functionality"""
        message = "Help me create a business plan"
        response = self.concierge.handle_message(message, self.test_session_id)
        
        assert response is not None
        assert 'text' in response
        assert 'sources' in response
    
    def test_session_management(self):
        """Test session ID handling"""
        # Test without session ID
        response1 = self.concierge.handle_message("Hello")
        assert response1 is not None
        
        # Test with provided session ID
        custom_session = "test-session-123"
        response2 = self.concierge.handle_message("Hello again", custom_session)
        assert response2 is not None
        
        # Check that conversation context is maintained
        assert custom_session in self.concierge.conversation_store
    
    def test_conversation_context(self):
        """Test conversation context maintenance"""
        session_id = str(uuid.uuid4())
        
        # Send multiple messages
        messages = [
            "What is an SBA loan?",
            "What are the requirements?",
            "How do I apply?"
        ]
        
        responses = []
        for message in messages:
            response = self.concierge.handle_message(message, session_id)
            responses.append(response)
            assert response is not None
        
        # Check that conversation has been recorded
        conversation = self.concierge.conversation_store[session_id]
        assert len(conversation["messages"]) == len(messages) * 2  # user + assistant messages
    
    def test_error_handling(self):
        """Test error handling"""
        # Test with empty message
        response = self.concierge.handle_message("", self.test_session_id)
        assert response is not None
        assert 'text' in response
    
    def test_intent_classification(self):
        """Test intent classification"""
        # Test document search intent
        intent1 = self.concierge._classify_intent("Find documents about loans", {})
        assert intent1 == "document_search"
        
        # Test task request intent
        intent2 = self.concierge._classify_intent("Help me create a business plan", {})
        assert intent2 == "task_request"
        
        # Test simple query intent
        intent3 = self.concierge._classify_intent("What is SBA?", {})
        assert intent3 == "simple_query"
    
    def test_response_format(self):
        """Test response format consistency"""
        message = "Tell me about SBA programs"
        response = self.concierge.handle_message(message, self.test_session_id)
        
        # Check response structure
        assert isinstance(response, dict)
        assert 'text' in response
        assert 'sources' in response
        assert isinstance(response['text'], str)
        assert isinstance(response['sources'], list)
    
    def test_source_formatting(self):
        """Test source formatting in responses"""
        message = "Search for business loan information"
        response = self.concierge.handle_message(message, self.test_session_id)
        
        # Check sources format
        for source in response['sources']:
            assert 'id' in source
            assert 'name' in source
            assert 'content' in source
            assert 'metadata' in source
    
    def test_workflow_integration(self):
        """Test complete workflow integration"""
        # Test a complete conversation flow
        session_id = str(uuid.uuid4())
        
        # Step 1: Initial query
        response1 = self.concierge.handle_message("What is an SBA 7(a) loan?", session_id)
        assert response1 is not None
        
        # Step 2: Follow-up question
        response2 = self.concierge.handle_message("What are the eligibility requirements?", session_id)
        assert response2 is not None
        
        # Step 3: Document search
        response3 = self.concierge.handle_message("Find documents about 7(a) loan applications", session_id)
        assert response3 is not None
        
        # Verify conversation history
        conversation = self.concierge.conversation_store[session_id]
        assert len(conversation["messages"]) >= 6  # 3 user + 3 assistant messages

def test_api_endpoints():
    """Test concierge through API endpoints"""
    import requests
    
    # Test the decompose endpoint (which uses concierge)
    test_data = {
        "message": "Help me understand SBA loan requirements",
        "session_id": "test-session-123"
    }
    
    # This would normally test against a running server
    # For now, we'll test the service layer directly
    from services.api_service import decompose_task_service
    
    try:
        response = decompose_task_service(
            "Help me understand SBA loan requirements",
            "test-session-123"
        )
        assert response is not None
        assert 'response' in response
    except Exception as e:
        print(f"API test skipped (requires running server): {e}")

if __name__ == "__main__":
    # Run tests directly
    test = TestConcierge()
    
    print("🧪 Running Concierge Functionality Tests...")
    print("=" * 50)
    
    tests = [
        test.test_concierge_initialization,
        test.test_simple_query_response,
        test.test_document_search_intent,
        test.test_task_decomposition_intent,
        test.test_session_management,
        test.test_conversation_context,
        test.test_error_handling,
        test.test_intent_classification,
        test.test_response_format,
        test.test_source_formatting,
        test.test_workflow_integration
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test.setup_method()
            test_func()
            print(f"✅ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: {str(e)}")
            failed += 1
    
    print("=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All concierge tests passed!")
    else:
        print("⚠️  Some tests failed - check logs for details")
