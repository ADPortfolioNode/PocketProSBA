"""
TaskAssistant - Clone of Concierge, manages hierarchical task workflows and step assignment.
"""
from typing import Dict, Any, List, Optional
from src.assistants.concierge import Concierge

class TaskStep:
    def __init__(self, step_number: int, instruction: str, assistant_name: str):
        self.step_number = step_number
        self.instruction = instruction
        self.assistant_name = assistant_name
        self.status = "pending"
        self.result = None
        self.progress = 0

class Task:
    def __init__(self, name: str, instruction: str, admin_assistant: str):
        self.name = name
        self.instruction = instruction
        self.admin_assistant = admin_assistant
        self.progress = 0
        self.steps: List[TaskStep] = []
        self.status = "pending"
        self.result = None

    def add_step(self, step: TaskStep):
        self.steps.append(step)

    def update_progress(self):
        completed = sum(1 for s in self.steps if s.status == "completed")
        self.progress = int((completed / len(self.steps)) * 100) if self.steps else 0
        if completed == len(self.steps):
            self.status = "completed"

class TaskAssistant(Concierge):
    """Clone of Concierge, manages tasks and delegates steps to assistants recursively."""
    def __init__(self, name: str = "TaskAssistant"):
        super().__init__()
        self.name = name
        self.active_tasks: Dict[str, Task] = {}

    def create_task(self, name: str, instruction: str, admin_assistant: str, steps: List[Dict[str, Any]]):
        task = Task(name, instruction, admin_assistant)
        for idx, step in enumerate(steps, 1):
            task.add_step(TaskStep(idx, step["instruction"], step["assistant_name"]))
        self.active_tasks[name] = task
        return task

    def assign_step(self, task_name: str, step_number: int, assistant_name: str):
        task = self.active_tasks.get(task_name)
        if not task:
            return None
        for step in task.steps:
            if step.step_number == step_number:
                step.assistant_name = assistant_name
                step.status = "assigned"
                return step
        return None

    def complete_step(self, task_name: str, step_number: int, result: Any):
        task = self.active_tasks.get(task_name)
        if not task:
            return None
        for step in task.steps:
            if step.step_number == step_number:
                step.status = "completed"
                step.result = result
        task.update_progress()
        if task.status == "completed":
            task.result = [s.result for s in task.steps]

            # Persist completed task to vector store for future retrieval
            try:
                import requests
                # Example: create embedding from task result (pseudo-code, replace with real embedding logic)
                embedding = self.llm.embed(str(task.result)) if hasattr(self.llm, 'embed') else [0.0] * 768
                metadata = {
                    "task_name": task.name,
                    "instruction": task.instruction,
                    "admin_assistant": task.admin_assistant,
                    "steps": [s.instruction for s in task.steps],
                    "result": task.result
                }
                requests.post(
                    "http://localhost:5000/api/chroma/store_step_embedding",
                    json={
                        "step_id": task.name,
                        "embedding": embedding,
                        "metadata": metadata
                    },
                    timeout=5
                )
            except Exception as e:
                print(f"Warning: Failed to persist task embedding: {e}")

            # Clean up after completion
            del self.active_tasks[task_name]
        return task

    def get_task_status(self, task_name: str) -> Optional[Dict[str, Any]]:
        task = self.active_tasks.get(task_name)
        if not task:
            return None
        return {
            "name": task.name,
            "instruction": task.instruction,
            "admin_assistant": task.admin_assistant,
            "progress": task.progress,
            "steps": [
                {
                    "step_number": s.step_number,
                    "instruction": s.instruction,
                    "assistant_name": s.assistant_name,
                    "status": s.status,
                    "progress": s.progress,
                    "result": s.result
                } for s in task.steps
            ],
            "status": task.status,
            "result": task.result
        }

    def heartbeat(self) -> List[Dict[str, Any]]:
        """Return status of all active tasks for frontend display."""
        return [self.get_task_status(name) for name in self.active_tasks]
