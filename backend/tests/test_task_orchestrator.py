import pytest
import unittest.mock as mock
from services.task_orchestrator import TaskOrchestrator, StepAssistant, StepExecutionError
from services.memory_repository import MemoryRepository
from services.step_strategies import DocumentSearchStrategy, TaskDecompositionStrategy

class TestTaskOrchestrator:
    @pytest.fixture
    def mock_memory_repo(self):
        """Mock memory repository"""
        return mock.MagicMock(spec=MemoryRepository)

    @pytest.fixture
    def mock_step_assistant(self):
        """Mock step assistant"""
        assistant = mock.MagicMock(spec=StepAssistant)
        assistant.execute_step.return_value = ({"result": "success"}, [])
        return assistant

    @pytest.fixture
    def orchestrator(self, mock_memory_repo, mock_step_assistant):
        """Create test orchestrator"""
        step_assistants = {"test_step": mock_step_assistant}
        return TaskOrchestrator(step_assistants, mock_memory_repo)

    def test_execute_task_success(self, orchestrator, mock_memory_repo, mock_step_assistant):
        """Test successful task execution"""
        task_data = {"steps": [{"type": "test_step", "data": {"query": "test"}}]}

        result = orchestrator.execute_task("task_123", task_data)

        assert result == [{"result": "success"}]
        mock_step_assistant.execute_step.assert_called_once()
        mock_memory_repo.store_task_result.assert_called_once_with("task_123", [{"result": "success"}])

    def test_execute_task_step_failure(self, orchestrator, mock_memory_repo, mock_step_assistant):
        """Test task execution with step failure"""
        mock_step_assistant.execute_step.side_effect = StepExecutionError("Step failed")

        task_data = {"steps": [{"type": "test_step", "data": {"query": "test"}}]}

        with pytest.raises(StepExecutionError):
            orchestrator.execute_task("task_123", task_data)

    def test_execute_task_unknown_step_type(self, orchestrator):
        """Test task execution with unknown step type"""
        task_data = {"steps": [{"type": "unknown_step", "data": {"query": "test"}}]}

        with pytest.raises(StepExecutionError, match="No assistant for step type 'unknown_step'"):
            orchestrator.execute_task("task_123", task_data)

    def test_decompose_task(self, orchestrator):
        """Test task decomposition"""
        task_data = {"steps": [{"type": "test_step", "data": {"query": "test"}}]}

        steps = orchestrator.decompose_task(task_data)

        assert steps == [{"type": "test_step", "data": {"query": "test"}}]

class TestStepAssistant:
    @pytest.fixture
    def mock_strategy(self):
        """Mock strategy"""
        strategy = mock.MagicMock()
        strategy.execute.return_value = {"result": "success"}
        strategy.validate.return_value = True
        return strategy

    @pytest.fixture
    def step_assistant(self, mock_strategy):
        """Create test step assistant"""
        return StepAssistant("test_step", [mock_strategy])

    def test_execute_step_success(self, step_assistant, mock_strategy):
        """Test successful step execution"""
        step_data = {"query": "test"}

        result, attempt_logs = step_assistant.execute_step(step_data)

        assert result == {"result": "success"}
        assert len(attempt_logs) == 1
        assert attempt_logs[0]["success"] is True
        mock_strategy.execute.assert_called_once_with(step_data)
        mock_strategy.validate.assert_called_once_with({"result": "success"})

    def test_execute_step_validation_failure(self, step_assistant, mock_strategy):
        """Test step execution with validation failure"""
        mock_strategy.validate.return_value = False
        step_data = {"query": "test"}

        with pytest.raises(StepExecutionError, match="Step 'test_step' failed after 3 attempts"):
            step_assistant.execute_step(step_data)

        assert mock_strategy.execute.call_count == 3
        assert mock_strategy.validate.call_count == 3

    def test_execute_step_execution_failure(self, step_assistant, mock_strategy):
        """Test step execution with execution failure"""
        mock_strategy.execute.side_effect = Exception("Execution failed")
        step_data = {"query": "test"}

        with pytest.raises(StepExecutionError, match="Step 'test_step' failed after 3 attempts"):
            step_assistant.execute_step(step_data)

        assert mock_strategy.execute.call_count == 3

    def test_execute_step_multiple_strategies(self):
        """Test step execution with multiple strategies"""
        strategy1 = mock.MagicMock()
        strategy1.execute.return_value = {"result": "fail"}
        strategy1.validate.return_value = False

        strategy2 = mock.MagicMock()
        strategy2.execute.return_value = {"result": "success"}
        strategy2.validate.return_value = True

        step_assistant = StepAssistant("test_step", [strategy1, strategy2])

        step_data = {"query": "test"}
        result, attempt_logs = step_assistant.execute_step(step_data)

        assert result == {"result": "success"}
        assert len(attempt_logs) == 1
        strategy1.execute.assert_called_once()
        strategy2.execute.assert_called_once()
