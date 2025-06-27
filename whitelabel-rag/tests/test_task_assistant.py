"""
Tests for TaskAssistant functionality
"""

import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def task_assistant(mock_llm_factory):
    """Create TaskAssistant instance with mocked dependencies."""
    pass

def test_task_step_creation():
    """Test TaskStep creation and basic functionality."""
    step = TaskStep(
        step_number=1,
        instruction="Test instruction",
        suggested_agent_type="SearchAgent",
        dependencies=[],
        metadata={"complexity": "low"}
    )
    assert step.step_number == 1
    assert step.instruction == "Test instruction"
    assert step.suggested_agent_type == "SearchAgent"
    assert step.status == "pending"
    assert step.dependencies == []
    assert step.metadata["complexity"] == "low"

def test_task_creation():
    """Test Task creation and step management."""
    task = Task("test-task-id", "Test task request", "test-session")
    assert task.task_id == "test-task-id"
    assert task.original_request == "Test task request"
    assert task.user_session == "test-session"
    assert task.status == "created"
    assert len(task.steps) == 0

def test_task_add_step():
    """Test adding steps to a task."""
    task = Task("test-task-id", "Test task request")
    step = TaskStep(1, "Test step", "SearchAgent")
    
    task.add_step(step)
    assert len(task.steps) == 1
    assert task.steps[0] == step

def test_task_get_ready_steps():
    """Test getting ready steps based on dependencies."""
    task = Task("test-task-id", "Test task request")
    
    # Add steps with dependencies
    step1 = TaskStep(1, "Step 1", "SearchAgent", [])
    step2 = TaskStep(2, "Step 2", "FileAgent", [1])
    step3 = TaskStep(3, "Step 3", "FunctionAgent", [])
    
    task.add_step(step1)
    task.add_step(step2)
    task.add_step(step3)
    
    # Initially, steps 1 and 3 should be ready (no dependencies)
    ready_steps = task.get_ready_steps()
    assert len(ready_steps) == 2
    assert step1 in ready_steps
    assert step3 in ready_steps
    
    # Complete step 1
    step1.status = "completed"
    
    # Now step 2 should also be ready
    ready_steps = task.get_ready_steps()
    assert len(ready_steps) == 2  # step2 and step3
    assert step2 in ready_steps
    assert step3 in ready_steps

def test_task_is_completed():
    """Test task completion detection."""
    task = Task("test-task-id", "Test task request")
    
    step1 = TaskStep(1, "Step 1", "SearchAgent")
    step2 = TaskStep(2, "Step 2", "FileAgent")
    
    task.add_step(step1)
    task.add_step(step2)
    
    # Task should not be completed initially
    assert not task.is_completed()
    
    # Complete one step
    step1.status = "completed"
    assert not task.is_completed()
    
    # Complete all steps
    step2.status = "completed"
    assert task.is_completed()

def test_task_assistant_initialization(task_assistant):
    """Test TaskAssistant initialization."""
    assert task_assistant.name == "TaskAssistant"
    assert hasattr(task_assistant, 'active_tasks')
    assert hasattr(task_assistant, 'config')
    assert task_assistant.config['max_steps'] == 10

def test_task_assistant_handle_message_validation(task_assistant):
    """Test TaskAssistant input validation."""
    # Test empty message
    result = task_assistant.handle_message("")
    assert result['error'] is True
    assert 'Empty message' in result['text']
    
    # Test None message
    result = task_assistant.handle_message(None)
    assert result['error'] is True
    assert 'Invalid message format' in result['text']

def test_task_assistant_decompose_task(task_assistant, mock_llm_factory):
    """Test task decomposition functionality."""
    # Mock LLM response for task decomposition
    mock_decomposition = '''{
        "task_analysis": "Simple task requiring file operations",
        "estimated_duration": "5 minutes",
        "steps": [
            {
                "step_number": 1,
                "instruction": "List available files",
                "suggested_agent_type": "FileAgent",
                "dependencies": [],
                "complexity": "low",
                "estimated_time": "30"
            },
            {
                "step_number": 2,
                "instruction": "Read the first file",
                "suggested_agent_type": "FileAgent",
                "dependencies": [1],
                "complexity": "medium",
                "estimated_time": "60"
            }
        ]
    }'''
    
    mock_llm_factory.generate_response.return_value = mock_decomposition
    
    # Create a task and test decomposition
    task = Task("test-task", "List and read files")
    result = task_assistant._decompose_task(task)
    
    assert result['success'] is True
    assert result['steps'] == 2
    assert len(task.steps) == 2
    assert task.steps[0].instruction == "List available files"
    assert task.steps[1].suggested_agent_type == "FileAgent"
    assert task.steps[1].dependencies == [1]

def test_task_assistant_get_agent_for_step(task_assistant):
    """Test agent selection for different step types."""
    # Test SearchAgent
    step = TaskStep(1, "Search test", "SearchAgent")
    with patch('app.services.search_agent.get_search_agent_instance') as mock_search:
        mock_agent = MagicMock()
        mock_search.return_value = mock_agent
        agent = task_assistant._get_agent_for_step(step)
        assert agent == mock_agent
        mock_search.assert_called_once()
    
    # Test FileAgent
    step = TaskStep(2, "File test", "FileAgent")
    with patch('app.services.file_agent.get_file_agent_instance') as mock_file:
        mock_agent = MagicMock()
        mock_file.return_value = mock_agent
        agent = task_assistant._get_agent_for_step(step)
        assert agent == mock_agent
        mock_file.assert_called_once()
    
    # Test unknown agent type
    step = TaskStep(3, "Unknown test", "UnknownAgent")
    agent = task_assistant._get_agent_for_step(step)
    assert agent is None

def test_task_assistant_execute_step(task_assistant):
    """Test individual step execution."""
    step = TaskStep(1, "Test step", "SearchAgent")
    task = Task("test-task", "Test task")
    
    # Mock agent
    mock_agent = MagicMock()
    mock_agent.handle_message.return_value = {
        'text': 'Step completed successfully',
        'success': True
    }
    
    with patch.object(task_assistant, '_get_agent_for_step', return_value=mock_agent):
        result = task_assistant._execute_step(step, task)
        
        assert result['success'] is True
        assert result['result'] == 'Step completed successfully'
        assert step.status == "completed"
        assert step.result == 'Step completed successfully'

def test_task_assistant_execute_step_failure(task_assistant):
    """Test step execution with failure and retry."""
    step = TaskStep(1, "Test step", "SearchAgent")
    task = Task("test-task", "Test task")
    
    # Mock agent that fails
    mock_agent = MagicMock()
    mock_agent.handle_message.return_value = {
        'text': 'Step failed',
        'error': True,
        'success': False
    }
    
    with patch.object(task_assistant, '_get_agent_for_step', return_value=mock_agent):
        result = task_assistant._execute_step(step, task)
        
        assert result['success'] is False
        assert 'Step failed' in result['error']
        assert step.retry_count == 1
        assert step.status == "pending"  # Should be pending for retry

def test_task_assistant_compile_final_result(task_assistant, mock_llm_factory):
    """Test final result compilation."""
    task = Task("test-task", "Test task")
    
    # Add completed steps
    step1 = TaskStep(1, "Step 1", "SearchAgent")
    step1.status = "completed"
    step1.result = "Found information"
    
    step2 = TaskStep(2, "Step 2", "FileAgent")
    step2.status = "completed"
    step2.result = "Processed file"
    
    task.add_step(step1)
    task.add_step(step2)
    
    mock_llm_factory.generate_response.return_value = "Comprehensive final result"
    
    step_results = [
        {'success': True, 'result': 'Found information'},
        {'success': True, 'result': 'Processed file'}
    ]
    
    result = task_assistant._compile_final_result(task, step_results)
    assert result == "Comprehensive final result"

def test_task_assistant_get_task_status(task_assistant):
    """Test getting task status."""
    task = Task("test-task", "Test task")
    task_assistant.active_tasks["test-task"] = task
    
    status = task_assistant.get_task_status("test-task")
    assert status is not None
    assert status['task_id'] == "test-task"
    assert status['original_request'] == "Test task"
    
    # Test non-existent task
    status = task_assistant.get_task_status("non-existent")
    assert status is None

def test_task_assistant_cancel_task(task_assistant):
    """Test task cancellation."""
    task = Task("test-task", "Test task")
    step = TaskStep(1, "Running step", "SearchAgent")
    step.status = "running"
    task.add_step(step)
    
    task_assistant.active_tasks["test-task"] = task
    
    result = task_assistant.cancel_task("test-task")
    assert result is True
    assert task.status == "cancelled"
    assert step.status == "cancelled"
    
    # Test cancelling non-existent task
    result = task_assistant.cancel_task("non-existent")
    assert result is False

def test_get_last_tasks(task_assistant):
    """Test get_last_tasks method returns last 3 tasks sorted by created_at descending."""
    from datetime import timedelta, datetime
    
    # Clear active_tasks
    task_assistant.active_tasks.clear()
    
    # No tasks
    result = task_assistant.get_last_tasks()
    assert result == []
    
    # Add 2 tasks
    task1 = Task("task1", "Request 1")
    task1.created_at = datetime.now() - timedelta(minutes=10)
    task2 = Task("task2", "Request 2")
    task2.created_at = datetime.now() - timedelta(minutes=5)
    task_assistant.active_tasks["task1"] = task1
    task_assistant.active_tasks["task2"] = task2
    
    result = task_assistant.get_last_tasks()
    assert len(result) == 2
    assert result[0]['task_id'] == "task2"  # Most recent first
    assert result[1]['task_id'] == "task1"
    
    # Add 2 more tasks
    task3 = Task("task3", "Request 3")
    task3.created_at = datetime.now() - timedelta(minutes=3)
    task4 = Task("task4", "Request 4")
    task4.created_at = datetime.now() - timedelta(minutes=1)
    task_assistant.active_tasks["task3"] = task3
    task_assistant.active_tasks["task4"] = task4
    
    result = task_assistant.get_last_tasks()
    assert len(result) == 3  # Only last 3
    assert result[0]['task_id'] == "task4"
    assert result[1]['task_id'] == "task3"
    assert result[2]['task_id'] == "task2"
    
    # Check keys in returned dict
    keys = {"task_id", "original_request", "user_session", "steps", "status", "created_at", "completed_at", "final_result", "execution_plan"}
    for task_dict in result:
        assert keys.issubset(task_dict.keys())
