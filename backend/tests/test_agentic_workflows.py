import pytest
import json
from unittest.mock import patch, MagicMock
from services.api_service import (
    decompose_task_service,
    execute_step_service,
    validate_step_service,
    query_documents_service,
    get_system_info_service
)

class TestAgenticWorkflows:
    """Test suite for agentic RAG workflows"""

    def test_decompose_task_service_success(self):
        """Test successful task decomposition workflow"""
        with patch('services.api_service.Concierge') as mock_concierge_class:
            mock_concierge = MagicMock()
            mock_concierge.handle_message.return_value = {
                'text': 'Task decomposed into steps',
                'sources': ['source1', 'source2'],
                'timestamp': '2024-01-01T00:00:00Z'
            }
            mock_concierge_class.return_value = mock_concierge

            result = decompose_task_service("Help me with SBA loans", "session123")

            assert result['response']['text'] == 'Task decomposed into steps'
            assert len(result['response']['sources']) == 2
            assert result['response']['timestamp'] == '2024-01-01T00:00:00Z'
            mock_concierge.handle_message.assert_called_once_with("Help me with SBA loans", "session123")

    def test_decompose_task_service_error_handling(self):
        """Test error handling in task decomposition"""
        with patch('services.api_service.Concierge') as mock_concierge_class:
            mock_concierge = MagicMock()
            mock_concierge.handle_message.side_effect = Exception("Agent error")
            mock_concierge_class.return_value = mock_concierge

            with pytest.raises(Exception, match="Failed to process message"):
                decompose_task_service("Help me", "session123")

    def test_execute_step_service_search_agent_success(self):
        """Test step execution with SearchAgent"""
        with patch('services.api_service.SearchAgent') as mock_search_class:
            mock_search_agent = MagicMock()
            mock_search_agent.handle_message.return_value = {
                'text': 'Search results found',
                'sources': ['doc1', 'doc2']
            }
            mock_search_class.return_value = mock_search_agent

            task = {
                'step_number': 1,
                'instruction': 'Search for SBA programs',
                'suggested_agent_type': 'SearchAgent'
            }

            result = execute_step_service(task)

            assert result['step_number'] == 1
            assert result['status'] == 'completed'
            assert result['result'] == 'Search results found'
            assert len(result['sources']) == 2
            mock_search_agent.handle_message.assert_called_once_with('Search for SBA programs')

    def test_execute_step_service_fallback_to_concierge(self):
        """Test fallback to Concierge when SearchAgent fails"""
        with patch('services.api_service.SearchAgent') as mock_search_class, \
             patch('services.api_service.Concierge') as mock_concierge_class:

            mock_search_class.side_effect = ValueError("SearchAgent unavailable")
            mock_concierge = MagicMock()
            mock_concierge.handle_message.return_value = {
                'text': 'Concierge handled the request',
                'sources': ['fallback_source']
            }
            mock_concierge_class.return_value = mock_concierge

            task = {
                'step_number': 2,
                'instruction': 'Handle this request',
                'suggested_agent_type': 'SearchAgent'
            }

            result = execute_step_service(task)

            assert result['status'] == 'completed'
            assert result['result'] == 'Concierge handled the request'
            mock_concierge.handle_message.assert_called_once_with('Handle this request')

    def test_execute_step_service_concierge_direct(self):
        """Test step execution with Concierge directly"""
        with patch('services.api_service.Concierge') as mock_concierge_class:
            mock_concierge = MagicMock()
            mock_concierge.handle_message.return_value = {
                'text': 'Concierge response',
                'sources': []
            }
            mock_concierge_class.return_value = mock_concierge

            task = {
                'step_number': 3,
                'instruction': 'General inquiry',
                'suggested_agent_type': 'Concierge'
            }

            result = execute_step_service(task)

            assert result['status'] == 'completed'
            assert result['result'] == 'Concierge response'

    def test_execute_step_service_missing_instruction(self):
        """Test error when instruction is missing"""
        task = {
            'step_number': 1,
            'suggested_agent_type': 'SearchAgent'
        }

        with pytest.raises(Exception, match="Instruction is required"):
            execute_step_service(task)

    def test_validate_step_service_pass(self):
        """Test successful step validation"""
        result = "Valid step result"
        task = {'step': 'test step'}

        validation = validate_step_service(result, task)

        assert validation['status'] == 'PASS'
        assert validation['confidence'] == 0.9
        assert 'validated successfully' in validation['feedback']

    def test_validate_step_service_fail(self):
        """Test failed step validation"""
        result = ""
        task = {'step': 'test step'}

        validation = validate_step_service(result, task)

        assert validation['status'] == 'FAIL'
        assert validation['confidence'] == 0.2
        assert 'empty or invalid' in validation['feedback']

    def test_query_documents_service_success(self):
        """Test successful document query workflow"""
        mock_results = {
            "documents": [["Document content 1", "Document content 2"]],
            "ids": [["id1", "id2"]],
            "metadatas": [[{"title": "Doc1"}, {"title": "Doc2"}]],
            "distances": [[0.1, 0.2]]
        }

        with patch('services.api_service.get_rag_manager') as mock_get_rag:
            mock_rag_manager = MagicMock()
            mock_rag_manager.query_documents.return_value = mock_results
            mock_get_rag.return_value = mock_rag_manager

            result = query_documents_service("SBA loans", 5)

            assert result['success'] is True
            assert result['query'] == "SBA loans"
            assert len(result['results']) == 2
            assert result['results'][0]['content'] == "Document content 1"
            assert result['results'][0]['relevance_score'] == 0.9
            assert result['results'][1]['relevance_score'] == 0.8
            mock_rag_manager.query_documents.assert_called_once_with("SBA loans", n_results=5)

    def test_query_documents_service_error_handling(self):
        """Test error handling in document query"""
        with patch('services.api_service.get_rag_manager') as mock_get_rag:
            mock_rag_manager = MagicMock()
            mock_rag_manager.query_documents.side_effect = Exception("Query failed")
            mock_get_rag.return_value = mock_rag_manager

            with pytest.raises(Exception, match="Search failed"):
                query_documents_service("test query", 3)

    def test_get_system_info_service_rag_available(self):
        """Test system info with RAG available"""
        mock_stats = {"count": 150}

        with patch('services.api_service.get_rag_manager') as mock_get_rag:
            mock_rag_manager = MagicMock()
            mock_rag_manager.is_available.return_value = True
            mock_rag_manager.get_collection_stats.return_value = mock_stats
            mock_get_rag.return_value = mock_rag_manager

            result = get_system_info_service()

            assert result['service'] == 'PocketPro:SBA Edition'
            assert result['version'] == '1.0.0'
            assert result['status'] == 'operational'
            assert result['rag_status'] == 'available'
            assert result['document_count'] == 150

    def test_get_system_info_service_rag_unavailable(self):
        """Test system info with RAG unavailable"""
        with patch('services.api_service.get_rag_manager') as mock_get_rag:
            mock_rag_manager = MagicMock()
            mock_rag_manager.is_available.return_value = False
            mock_get_rag.return_value = mock_rag_manager

            result = get_system_info_service()

            assert result['rag_status'] == 'unavailable'
            assert result['document_count'] == 0

    def test_get_system_info_service_error_handling(self):
        """Test error handling in system info"""
        with patch('services.api_service.get_rag_manager') as mock_get_rag:
            mock_rag_manager = MagicMock()
            mock_rag_manager.is_available.side_effect = Exception("Connection failed")
            mock_get_rag.return_value = mock_rag_manager

            result = get_system_info_service()

            assert result['rag_status'] == 'unavailable'
            assert 'error' in result

    def test_end_to_end_workflow_integration(self):
        """Test end-to-end workflow integration"""
        # Mock all components
        with patch('services.api_service.Concierge') as mock_concierge_class, \
             patch('services.api_service.SearchAgent') as mock_search_class, \
             patch('services.api_service.get_rag_manager') as mock_get_rag:

            # Setup mocks
            mock_concierge = MagicMock()
            mock_concierge.handle_message.return_value = {
                'text': 'Task broken into steps',
                'sources': [],
                'timestamp': '2024-01-01T00:00:00Z'
            }
            mock_concierge_class.return_value = mock_concierge

            mock_search_agent = MagicMock()
            mock_search_agent.handle_message.return_value = {
                'text': 'Step executed successfully',
                'sources': ['source1']
            }
            mock_search_class.return_value = mock_search_agent

            mock_rag_manager = MagicMock()
            mock_rag_manager.is_available.return_value = True
            mock_rag_manager.get_collection_stats.return_value = {"count": 100}
            mock_get_rag.return_value = mock_rag_manager

            # Test system info
            system_info = get_system_info_service()
            assert system_info['rag_status'] == 'available'

            # Test task decomposition
            decomposed = decompose_task_service("Find SBA loan information", "session1")
            assert 'response' in decomposed

            # Test step execution
            step_result = execute_step_service({
                'step_number': 1,
                'instruction': 'Search for loan programs',
                'suggested_agent_type': 'SearchAgent'
            })
            assert step_result['status'] == 'completed'

            # Test validation
            validation = validate_step_service("Valid result", {})
            assert validation['status'] == 'PASS'

            # Verify all mocks were called
            assert mock_concierge.handle_message.call_count >= 1
            assert mock_search_agent.handle_message.call_count >= 1
            assert mock_rag_manager.is_available.call_count >= 1
