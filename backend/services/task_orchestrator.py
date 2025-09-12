"""
Task Orchestrator Service

Manages the lifecycle of tasks from submission to completion with feedback loops,
memory integration, and automated retries.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    DECOMPOSING = "decomposing"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class StepStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRIED = "retried"

@dataclass
class TaskStep:
    """Represents a single step in a task"""
    id: str
    task_id: str
    type: str
    data: Dict[str, Any]
    status: StepStatus
    strategy_used: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    execution_time: Optional[float] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Task:
    """Represents a complete task with steps"""
    id: str
    user_id: str
    message: str
    session_id: Optional[str]
    status: TaskStatus
    steps: List[TaskStep]
    current_step_index: int = 0
    memory_context: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.steps is None:
            self.steps = []

class TaskOrchestrator:
    """
    Main orchestrator for task lifecycle management with self-optimization
    """

    def __init__(self, memory_repository=None, feedback_manager=None, metrics_collector=None):
        self.memory_repository = memory_repository
        self.feedback_manager = feedback_manager
        self.metrics_collector = metrics_collector
        self.active_tasks: Dict[str, Task] = {}
        self.task_history: List[Task] = []

    def submit_task(self, user_id: str, message: str, session_id: Optional[str] = None) -> str:
        """
        Submit a new task for processing

        Args:
            user_id: User identifier
            message: Task description/message
            session_id: Optional session identifier

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        # Create new task
        task = Task(
            id=task_id,
            user_id=user_id,
            message=message,
            session_id=session_id,
            status=TaskStatus.PENDING,
            steps=[]
        )

        self.active_tasks[task_id] = task
        logger.info(f"Task {task_id} submitted by user {user_id}")

        # Start task processing asynchronously
        self._process_task_async(task_id)

        return task_id

    def _process_task_async(self, task_id: str):
        """Process task asynchronously"""
        try:
            task = self.active_tasks[task_id]

            # Phase 1: Task Decomposition
            task.status = TaskStatus.DECOMPOSING
            steps = self._decompose_task(task.message, task.session_id)

            if not steps:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task_id} failed: No steps generated")
                return

            task.steps = steps
            logger.info(f"Task {task_id} decomposed into {len(steps)} steps")

            # Phase 2: Execute Steps
            task.status = TaskStatus.EXECUTING
            success = self._execute_steps(task)

            # Phase 3: Final Validation
            if success:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                logger.info(f"Task {task_id} completed successfully")

                # Store in memory for learning
                if self.memory_repository:
                    self.memory_repository.store_task_result(task)
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task_id} failed execution")

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            task.status = TaskStatus.FAILED

    def _decompose_task(self, message: str, session_id: Optional[str]) -> List[TaskStep]:
        """
        Decompose user message into executable steps

        Args:
            message: User message
            session_id: Session identifier

        Returns:
            List of task steps
        """
        try:
            # Use existing decomposition service
            from services.api_service import decompose_task_service
            result = decompose_task_service(message, session_id)

            if not result or 'steps' not in result:
                return []

            steps = []
            for i, step_data in enumerate(result['steps']):
                step = TaskStep(
                    id=f"{result.get('task_id', 'unknown')}_step_{i}",
                    task_id=result.get('task_id', 'unknown'),
                    type=step_data.get('type', 'unknown'),
                    data=step_data.get('data', {}),
                    status=StepStatus.PENDING
                )
                steps.append(step)

            return steps

        except Exception as e:
            logger.error(f"Error decomposing task: {str(e)}")
            return []

    def _execute_steps(self, task: Task) -> bool:
        """
        Execute all steps in a task with feedback and retries

        Args:
            task: Task to execute

        Returns:
            True if all steps completed successfully
        """
        for i, step in enumerate(task.steps):
            task.current_step_index = i

            # Select optimal strategy for this step
            strategy = self._select_optimal_strategy(step)

            # Execute step with selected strategy
            success = self._execute_step_with_strategy(step, strategy)

            if not success:
                # Handle failure with retry logic
                if not self._handle_step_failure(task, step, i):
                    return False

        return True

    def _select_optimal_strategy(self, step: TaskStep) -> str:
        """
        Select the optimal strategy for a step based on memory and learning

        Args:
            step: Task step

        Returns:
            Strategy name
        """
        if not self.memory_repository:
            return "default"

        # Query memory for similar steps and their success rates
        similar_steps = self.memory_repository.find_similar_steps(step)

        if not similar_steps:
            return "default"

        # Calculate strategy performance
        strategy_performance = {}
        for similar_step in similar_steps:
            strategy = similar_step.get('strategy_used', 'default')
            success = similar_step.get('success', False)

            if strategy not in strategy_performance:
                strategy_performance[strategy] = {'success': 0, 'total': 0}

            strategy_performance[strategy]['total'] += 1
            if success:
                strategy_performance[strategy]['success'] += 1

        # Select strategy with highest success rate
        best_strategy = "default"
        best_rate = 0

        for strategy, stats in strategy_performance.items():
            rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
            if rate > best_rate:
                best_rate = rate
                best_strategy = strategy

        logger.info(f"Selected strategy '{best_strategy}' for step {step.type} (success rate: {best_rate:.2f})")
        return best_strategy

    def _execute_step_with_strategy(self, step: TaskStep, strategy: str) -> bool:
        """
        Execute a step using the selected strategy

        Args:
            step: Task step
            strategy: Strategy to use

        Returns:
            True if step executed successfully
        """
        try:
            step.status = StepStatus.EXECUTING
            step.strategy_used = strategy
            start_time = time.time()

            # Execute step using strategy
            from services.step_strategies import StepStrategyFactory
            strategy_instance = StepStrategyFactory.get_strategy(strategy)
            result = strategy_instance.execute(step)

            execution_time = time.time() - start_time
            step.execution_time = execution_time

            if result.get('success', False):
                step.status = StepStatus.COMPLETED
                step.result = result.get('data')
                logger.info(f"Step {step.id} completed successfully in {execution_time:.2f}s")
                return True
            else:
                step.status = StepStatus.FAILED
                step.error = result.get('error', 'Unknown error')
                logger.error(f"Step {step.id} failed: {step.error}")
                return False

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logger.error(f"Step {step.id} execution error: {str(e)}")
            return False

    def _handle_step_failure(self, task: Task, step: TaskStep, step_index: int) -> bool:
        """
        Handle step failure with retry logic

        Args:
            task: Parent task
            step: Failed step
            step_index: Index of failed step

        Returns:
            True if failure was handled (either retried or skipped)
        """
        if step.retry_count >= step.max_retries:
            logger.error(f"Step {step.id} exceeded max retries ({step.max_retries})")
            return False

        # Try alternative strategy
        alternative_strategy = self._select_alternative_strategy(step)
        if alternative_strategy != step.strategy_used:
            step.retry_count += 1
            step.status = StepStatus.RETRIED
            logger.info(f"Retrying step {step.id} with alternative strategy: {alternative_strategy}")

            success = self._execute_step_with_strategy(step, alternative_strategy)
            if success:
                return True

        # If all retries failed, mark task as failed
        task.status = TaskStatus.FAILED
        return False

    def _select_alternative_strategy(self, step: TaskStep) -> str:
        """
        Select an alternative strategy for retry

        Args:
            step: Failed step

        Returns:
            Alternative strategy name
        """
        # Simple strategy rotation for now
        strategies = ["default", "conservative", "aggressive", "adaptive"]
        current_index = strategies.index(step.strategy_used) if step.strategy_used in strategies else 0
        next_index = (current_index + 1) % len(strategies)
        return strategies[next_index]

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a task

        Args:
            task_id: Task identifier

        Returns:
            Task status information
        """
        task = self.active_tasks.get(task_id)
        if not task:
            return None

        return {
            'task_id': task.id,
            'status': task.status.value,
            'current_step': task.current_step_index,
            'total_steps': len(task.steps),
            'progress': (task.current_step_index / len(task.steps)) * 100 if task.steps else 0,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        }

    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a task

        Args:
            task_id: Task identifier

        Returns:
            Detailed task information
        """
        task = self.active_tasks.get(task_id)
        if not task:
            return None

        return {
            'task': asdict(task),
            'steps': [asdict(step) for step in task.steps]
        }

# Global orchestrator instance
_orchestrator_instance = None

def get_orchestrator():
    """Get the global task orchestrator instance"""
    global _orchestrator_instance

    if _orchestrator_instance is None:
        # Initialize with dependencies
        try:
            from services.memory_repository import MemoryRepository
            from services.feedback_manager import FeedbackManager
            from services.metrics_collector import MetricsCollector

            memory_repo = MemoryRepository()
            feedback_mgr = FeedbackManager()
            metrics_collector = MetricsCollector()

            _orchestrator_instance = TaskOrchestrator(
                memory_repository=memory_repo,
                feedback_manager=feedback_mgr,
                metrics_collector=metrics_collector
            )
        except ImportError:
            # Fallback without advanced features
            _orchestrator_instance = TaskOrchestrator()

    return _orchestrator_instance
