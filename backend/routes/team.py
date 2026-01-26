"""
Team Workflow Routes

API endpoints for the world-class three-person development team workflow.
"""

from flask import Blueprint, request, jsonify
import logging
from backend.services.team_workflow_service import get_team_workflow_service

logger = logging.getLogger(__name__)
team_bp = Blueprint('team', __name__)


@team_bp.route('/submit', methods=['POST'])
def submit_issue():
    """
    Submit a new issue for the team to work on.
    
    Expected JSON payload:
    {
        "issue_description": "Description of the issue to resolve"
    }
    
    Returns:
        JSON response with task_id and greeting
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        issue_description = data.get('issue_description')
        if not issue_description or not issue_description.strip():
            return jsonify({'error': 'Issue description is required'}), 400
        
        # Get the team workflow service
        service = get_team_workflow_service()
        
        # Submit the issue
        task = service.submit_issue(issue_description.strip())
        
        return jsonify({
            'task_id': task.id,
            'status': task.status.value,
            'greeting': service.greeting,
            'message': 'Issue submitted successfully. Team is ready to work!',
            'created_at': task.created_at.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting issue: {str(e)}")
        return jsonify({
            'error': 'Failed to submit issue',
            'message': str(e)
        }), 500


@team_bp.route('/process/<task_id>', methods=['POST'])
def process_task(task_id: str):
    """
    Process a task through the team workflow.
    
    Args:
        task_id: Task identifier
        
    Returns:
        JSON response with task status and results
    """
    try:
        service = get_team_workflow_service()
        
        # Process the task
        task = service.process_task(task_id)
        
        return jsonify({
            'task_id': task.id,
            'status': task.status.value,
            'iterations': task.iterations,
            'validation_passed': task.validation_passed,
            'solution': task.solution,
            'message': 'Task processing completed',
            'updated_at': task.updated_at.isoformat(),
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        }), 200
        
    except ValueError as e:
        logger.error(f"Task not found: {str(e)}")
        return jsonify({
            'error': 'Task not found',
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}")
        return jsonify({
            'error': 'Failed to process task',
            'message': str(e)
        }), 500


@team_bp.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """
    Get the current status of a task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        JSON response with task status
    """
    try:
        service = get_team_workflow_service()
        status = service.get_task_status(task_id)
        
        if not status:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return jsonify({
            'error': 'Failed to get task status',
            'message': str(e)
        }), 500


@team_bp.route('/task/<task_id>/history', methods=['GET'])
def get_conversation_history(task_id: str):
    """
    Get the conversation history for a task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        JSON response with conversation history
    """
    try:
        service = get_team_workflow_service()
        history = service.get_conversation_history(task_id)
        
        if history is None:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({
            'task_id': task_id,
            'greeting': service.greeting,
            'conversation': history,
            'message_count': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return jsonify({
            'error': 'Failed to get conversation history',
            'message': str(e)
        }), 500


@team_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    List all active tasks.
    
    Returns:
        JSON response with list of active tasks
    """
    try:
        service = get_team_workflow_service()
        
        tasks_info = []
        for task_id, task in service.active_tasks.items():
            tasks_info.append({
                'task_id': task.id,
                'status': task.status.value,
                'iterations': task.iterations,
                'validation_passed': task.validation_passed,
                'issue_description': task.issue_description[:100] + '...' if len(task.issue_description) > 100 else task.issue_description,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            })
        
        return jsonify({
            'greeting': service.greeting,
            'tasks': tasks_info,
            'count': len(tasks_info)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        return jsonify({
            'error': 'Failed to list tasks',
            'message': str(e)
        }), 500


@team_bp.route('/health', methods=['GET'])
def team_health():
    """
    Health check for team workflow service.
    
    Returns:
        JSON response with health status
    """
    try:
        service = get_team_workflow_service()
        
        health_info = {
            'status': 'healthy',
            'service': 'team_workflow',
            'greeting': service.greeting,
            'active_tasks': len(service.active_tasks),
            'message': 'World-class development team ready to assist!'
        }
        
        return jsonify(health_info), 200
        
    except Exception as e:
        logger.error(f"Team workflow health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'team_workflow',
            'error': str(e)
        }), 500
