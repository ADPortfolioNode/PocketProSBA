"""
Orchestrator Routes

API endpoints for task orchestration, monitoring, and management.
"""

from flask import Blueprint, request, jsonify
import logging
from backend.services.task_orchestrator import get_orchestrator

logger = logging.getLogger(__name__)
orchestrator_bp = Blueprint('orchestrator', __name__)

@orchestrator_bp.route('/submit', methods=['POST'])
def submit_task():
    """
    Submit a new task for orchestration

    Expected JSON payload:
    {
        "user_id": "user123",
        "message": "Help me find SBA loan information",
        "session_id": "optional-session-id"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        user_id = data.get('user_id')
        message = data.get('message')
        session_id = data.get('session_id')

        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400

        if not message or not message.strip():
            return jsonify({'error': 'Message content is required'}), 400

        orchestrator = get_orchestrator()
        task_id = orchestrator.submit_task(user_id, message.strip(), session_id)

        return jsonify({
            'task_id': task_id,
            'status': 'submitted',
            'message': 'Task submitted for orchestration'
        }), 201

    except Exception as e:
        logger.error(f"Error submitting task: {str(e)}")
        return jsonify({
            'error': 'Failed to submit task',
            'message': str(e)
        }), 500

@orchestrator_bp.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """
    Get the current status of a task

    Args:
        task_id: Task identifier
    """
    try:
        orchestrator = get_orchestrator()
        status = orchestrator.get_task_status(task_id)

        if not status:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return jsonify({
            'error': 'Failed to get task status',
            'message': str(e)
        }), 500

@orchestrator_bp.route('/task/<task_id>/details', methods=['GET'])
def get_task_details(task_id: str):
    """
    Get detailed information about a task

    Args:
        task_id: Task identifier
    """
    try:
        orchestrator = get_orchestrator()
        details = orchestrator.get_task_details(task_id)

        if not details:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(details), 200

    except Exception as e:
        logger.error(f"Error getting task details: {str(e)}")
        return jsonify({
            'error': 'Failed to get task details',
            'message': str(e)
        }), 500

@orchestrator_bp.route('/tasks', methods=['GET'])
def list_active_tasks():
    """
    List all active tasks
    """
    try:
        orchestrator = get_orchestrator()

        # Get basic info for all active tasks
        tasks_info = []
        for task_id, task in orchestrator.active_tasks.items():
            tasks_info.append({
                'task_id': task_id,
                'user_id': task.user_id,
                'status': task.status.value,
                'message': task.message[:100] + '...' if len(task.message) > 100 else task.message,
                'created_at': task.created_at.isoformat(),
                'current_step': task.current_step_index,
                'total_steps': len(task.steps)
            })

        return jsonify({
            'tasks': tasks_info,
            'count': len(tasks_info)
        }), 200

    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        return jsonify({
            'error': 'Failed to list tasks',
            'message': str(e)
        }), 500

@orchestrator_bp.route('/strategies', methods=['GET'])
def get_available_strategies():
    """
    Get list of available execution strategies
    """
    try:
    from backend.services.step_strategies import StepStrategyFactory

        strategies = StepStrategyFactory.get_available_strategies()
        strategy_info = []

        for strategy_name in strategies:
            info = StepStrategyFactory.get_strategy_info(strategy_name)
            if info:
                strategy_info.append(info)

        return jsonify({
            'strategies': strategy_info,
            'count': len(strategy_info)
        }), 200

    except Exception as e:
        logger.error(f"Error getting strategies: {str(e)}")
        return jsonify({
            'error': 'Failed to get strategies',
            'message': str(e)
        }), 500

@orchestrator_bp.route('/memory/stats', methods=['GET'])
def get_memory_stats():
    """
    Get memory repository statistics
    """
    try:
        orchestrator = get_orchestrator()
        if orchestrator.memory_repository:
            stats = orchestrator.memory_repository.get_memory_stats()
            return jsonify(stats), 200
        else:
            return jsonify({
                'error': 'Memory repository not available'
            }), 503

    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        return jsonify({
            'error': 'Failed to get memory stats',
            'message': str(e)
        }), 500

@orchestrator_bp.route('/memory/cleanup', methods=['POST'])
def cleanup_memory():
    """
    Clean up old memory entries

    Expected JSON payload:
    {
        "days_to_keep": 30
    }
    """
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 30)

        orchestrator = get_orchestrator()
        if orchestrator.memory_repository:
            orchestrator.memory_repository.cleanup_old_memory(days_to_keep)
            return jsonify({
                'message': f'Memory cleanup initiated, keeping data from last {days_to_keep} days'
            }), 200
        else:
            return jsonify({
                'error': 'Memory repository not available'
            }), 503

    except Exception as e:
        logger.error(f"Error during memory cleanup: {str(e)}")
        return jsonify({
            'error': 'Failed to cleanup memory',
            'message': str(e)
        }), 500

@orchestrator_bp.route('/health', methods=['GET'])
def orchestrator_health():
    """
    Health check for orchestrator service
    """
    try:
        orchestrator = get_orchestrator()

        health_info = {
            'status': 'healthy',
            'service': 'orchestrator',
            'active_tasks': len(orchestrator.active_tasks),
            'memory_available': orchestrator.memory_repository is not None,
            'feedback_available': orchestrator.feedback_manager is not None,
            'metrics_available': orchestrator.metrics_collector is not None
        }

        return jsonify(health_info), 200

    except Exception as e:
        logger.error(f"Orchestrator health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'orchestrator',
            'error': str(e)
        }), 500
