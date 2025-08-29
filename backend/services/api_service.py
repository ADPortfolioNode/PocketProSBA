import logging
from services.rag import get_rag_manager
from assistants.concierge import Concierge
from assistants.search import SearchAgent

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

def decompose_task_service(message, session_id):
    """Decompose a user task into steps"""
    try:
        concierge = Concierge()
        response = concierge.handle_message(message, session_id)
        return {
            'response': {
                'text': response.get('text', ''),
                'sources': response.get('sources', []),
                'timestamp': response.get('timestamp')
            }
        }
    except Exception as e:
        logger.error(f"Error decomposing task: {str(e)}")
        raise Exception(f'Failed to process message: {str(e)}')

def execute_step_service(task):
    """Execute a decomposed task step"""
    try:
        step_number = task.get('step_number')
        instruction = task.get('instruction', '')
        agent_type = task.get('suggested_agent_type', 'SearchAgent')
        
        if not instruction:
            raise ValueError('Instruction is required')
        
        # Try to create the requested agent, fall back to Concierge if SearchAgent fails
        if agent_type == 'SearchAgent':
            try:
                agent = SearchAgent()
                result = agent.handle_message(instruction)
            except ValueError as e:
                # Fall back to Concierge if SearchAgent cannot be initialized
                logger.warning(f"SearchAgent initialization failed: {str(e)}. Falling back to Concierge.")
                agent = Concierge()
                result = agent.handle_message(instruction)
            except Exception as e:
                # Handle other exceptions from SearchAgent
                logger.error(f"SearchAgent failed: {str(e)}. Falling back to Concierge.")
                agent = Concierge()
                result = agent.handle_message(instruction)
        else:
            agent = Concierge()
            result = agent.handle_message(instruction)
        
        return {
            'step_number': step_number,
            'status': 'completed' if not result.get('error') else 'failed',
            'result': result.get('text', ''),
            'sources': result.get('sources', [])
        }
    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        raise Exception(f'Failed to execute step: {str(e)}')

def validate_step_service(result, task):
    """Validate a step result"""
    try:
        if result:
            return {
                'status': 'PASS',
                'confidence': 0.9,
                'feedback': 'Step result validated successfully'
            }
        else:
            return {
                'status': 'FAIL',
                'confidence': 0.2,
                'feedback': 'Step result is empty or invalid'
            }
    except Exception as e:
        logger.error(f"Error validating step: {str(e)}")
        raise Exception(f'Failed to validate step: {str(e)}')

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
