import os
import logging
import time
import json
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base import BaseAssistant

# Configure logging
logger = logging.getLogger(__name__)

class TaskAssistant(BaseAssistant):
    """
    Task Assistant

    Handles complex, multi-step task coordination and execution.
    Breaks down tasks into logical steps, manages specialized assistants,
    and validates results.
    """

    def __init__(self):
        """Initialize the Task assistant"""
        super().__init__("TaskAssistant")
        self.active_tasks = {}
        self.max_steps = 10  # Maximum steps per task
        self.max_retries = 3  # Maximum retries per step

        # Initialize RAG manager for context
        try:
            from backend.services.rag import get_rag_manager
            self.rag_manager = get_rag_manager()
        except Exception as e:
            logger.error(f"Failed to initialize RAG manager: {str(e)}")
            self.rag_manager = None

        # Initialize conversation store
        try:
            from backend.services.conversation_store import get_conversation_store
            self.conversation_store = get_conversation_store()
        except Exception as e:
            logger.error(f"Failed to initialize conversation store: {str(e)}")
            self.conversation_store = None

    def handle_message(self, message: str, task_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle a complex task request

        Args:
            message: The task description
            task_id: Optional existing task ID for continuation
            context: Additional context information

        Returns:
            Task execution results
        """
        try:
            self._update_status("analyzing", 10, "Analyzing task requirements...")

            # Generate or use existing task ID
            if not task_id:
                task_id = str(uuid.uuid4())

            # Get conversation context if available
            session_id = context.get("session_id") if context else None
            conversation_history = []
            if session_id and self.conversation_store:
                conversation_history = self.conversation_store.get_recent_messages(session_id, limit=10)

            # Initialize task tracking
            if task_id not in self.active_tasks:
                self.active_tasks[task_id] = {
                    "task_id": task_id,
                    "original_message": message,
                    "status": "initializing",
                    "steps": [],
                    "results": [],
                    "created_at": datetime.now().isoformat(),
                    "context": context or {},
                    "conversation_history": conversation_history
                }

            task = self.active_tasks[task_id]

            # Decompose task into steps
            self._update_status("planning", 20, "Breaking down task into steps...")
            steps = self._decompose_task(message)

            if not steps:
                return self.report_failure("Unable to decompose task into executable steps")

            task["steps"] = steps
            task["status"] = "planning"

            # Execute steps
            self._update_status("executing", 30, "Executing task steps...")
            results = self._execute_task_steps(task_id, steps)

            # Validate and compile results
            self._update_status("validating", 80, "Validating results...")
            final_result = self._compile_results(task_id, results)

            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            self._update_status("completed", 100, "Task completed successfully")

            return self.report_success(
                text=final_result["text"],
                sources=final_result.get("sources", []),
                additional_data={
                    "task_id": task_id,
                    "steps_executed": len(results),
                    "execution_time": time.time() - time.time(),  # Would need to track start time
                    "results": results
                }
            )

        except Exception as e:
            logger.error(f"Task execution error: {str(e)}")
            return self.report_failure(f"Task execution failed: {str(e)}")

    def _decompose_task(self, message: str) -> List[Dict[str, Any]]:
        """
        Decompose a task into executable steps

        Args:
            message: Task description

        Returns:
            List of step dictionaries
        """
        message_lower = message.lower()
        steps = []

        # Analyze task complexity and create appropriate steps
        if self._is_simple_search_task(message_lower):
            steps.append({
                "step_number": 1,
                "description": "Search for relevant information",
                "agent_type": "SearchAgent",
                "instruction": message,
                "required": True,
                "max_retries": 2
            })

        elif self._is_file_operation_task(message_lower):
            steps.append({
                "step_number": 1,
                "description": "Handle file operations",
                "agent_type": "FileAgent",
                "instruction": message,
                "required": True,
                "max_retries": 2
            })

        elif self._is_function_task(message_lower):
            steps.append({
                "step_number": 1,
                "description": "Execute required function",
                "agent_type": "FunctionAgent",
                "instruction": message,
                "required": True,
                "max_retries": 2
            })

        elif self._is_complex_business_task(message_lower):
            # Break down complex business tasks into multiple steps
            steps = self._create_business_task_steps(message)

        else:
            # Generic multi-step approach for complex tasks
            steps = self._create_generic_task_steps(message)

        return steps

    def _is_simple_search_task(self, message_lower: str) -> bool:
        """Check if task is a simple search"""
        search_keywords = ["find", "search", "look for", "information about", "tell me about"]
        return any(keyword in message_lower for keyword in search_keywords)

    def _is_file_operation_task(self, message_lower: str) -> bool:
        """Check if task involves file operations"""
        file_keywords = ["upload", "file", "document", "save", "download"]
        return any(keyword in message_lower for keyword in file_keywords)

    def _is_function_task(self, message_lower: str) -> bool:
        """Check if task requires function execution"""
        function_keywords = ["calculate", "compute", "time", "weather", "email", "format"]
        return any(keyword in message_lower for keyword in function_keywords)

    def _is_complex_business_task(self, message_lower: str) -> bool:
        """Check if task is a complex business-related task"""
        business_keywords = ["business plan", "loan", "grant", "sba", "startup", "marketing plan"]
        return any(keyword in message_lower for keyword in business_keywords)

    def _create_business_task_steps(self, message: str) -> List[Dict[str, Any]]:
        """Create steps for complex business tasks"""
        steps = []

        if "business plan" in message.lower():
            steps.extend([
                {
                    "step_number": 1,
                    "description": "Research SBA business planning resources",
                    "agent_type": "SearchAgent",
                    "instruction": "Find SBA resources for business planning and development",
                    "required": True,
                    "max_retries": 2
                },
                {
                    "step_number": 2,
                    "description": "Gather relevant templates and guides",
                    "agent_type": "SearchAgent",
                    "instruction": "Find business plan templates and planning guides",
                    "required": False,
                    "max_retries": 1
                }
            ])

        elif "loan" in message.lower():
            steps.extend([
                {
                    "step_number": 1,
                    "description": "Research SBA loan programs",
                    "agent_type": "SearchAgent",
                    "instruction": "Find information about SBA loan programs and requirements",
                    "required": True,
                    "max_retries": 2
                },
                {
                    "step_number": 2,
                    "description": "Check eligibility requirements",
                    "agent_type": "FunctionAgent",
                    "instruction": "Analyze loan eligibility based on business type and needs",
                    "required": False,
                    "max_retries": 1
                }
            ])

        return steps

    def _create_generic_task_steps(self, message: str) -> List[Dict[str, Any]]:
        """Create generic steps for complex tasks"""
        return [
            {
                "step_number": 1,
                "description": "Gather relevant information",
                "agent_type": "SearchAgent",
                "instruction": f"Research information related to: {message}",
                "required": True,
                "max_retries": 2
            },
            {
                "step_number": 2,
                "description": "Analyze and organize findings",
                "agent_type": "FunctionAgent",
                "instruction": f"Analyze and summarize the information gathered about: {message}",
                "required": False,
                "max_retries": 1
            }
        ]

    def _execute_task_steps(self, task_id: str, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute task steps with proper error handling and retries

        Args:
            task_id: Task identifier
            steps: List of steps to execute

        Returns:
            List of step execution results
        """
        results = []

        for step in steps:
            step_result = self._execute_single_step(task_id, step)
            results.append(step_result)

            # Stop execution if required step failed
            if step.get("required", False) and not step_result.get("success", False):
                logger.warning(f"Required step {step['step_number']} failed, stopping execution")
                break

        return results

    def _execute_single_step(self, task_id: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step with retry logic using REST API

        Args:
            task_id: Task identifier
            step: Step configuration

        Returns:
            Step execution result
        """
        step_number = step["step_number"]
        max_retries = min(step.get("max_retries", 2), self.max_retries)

        for attempt in range(max_retries + 1):
            try:
                self._update_status("executing", 40 + (step_number * 5),
                                  f"Executing step {step_number} (attempt {attempt + 1})...")

                # Get the API endpoint for this step
                api_endpoint = self._get_agent_for_step(step)
                if not api_endpoint:
                    return {
                        "step_number": step_number,
                        "success": False,
                        "error": f"Unknown agent type: {step['agent_type']}",
                        "attempts": attempt + 1
                    }

                # Make REST API call
                result = self._call_assistant_api(api_endpoint, step["instruction"])

                # Validate result
                if self._validate_step_result(result, step):
                    return {
                        "step_number": step_number,
                        "success": True,
                        "result": result,
                        "attempts": attempt + 1,
                        "execution_time": time.time()
                    }
                else:
                    logger.warning(f"Step {step_number} validation failed on attempt {attempt + 1}")

            except Exception as e:
                logger.error(f"Step {step_number} execution error on attempt {attempt + 1}: {str(e)}")

        # All retries exhausted
        return {
            "step_number": step_number,
            "success": False,
            "error": f"Step failed after {max_retries + 1} attempts",
            "attempts": max_retries + 1
        }

    def _get_agent_for_step(self, step: Dict[str, Any]) -> Optional[str]:
        """
        Get the API endpoint URL for a step

        Args:
            step: Step configuration

        Returns:
            API endpoint URL or None
        """
        agent_type = step["agent_type"]

        # Get base URL from environment or default to localhost
        base_url = os.getenv("API_BASE_URL", "http://localhost:5000/api")

        endpoints = {
            "SearchAgent": f"{base_url}/assistants/search",
            "FileAgent": f"{base_url}/assistants/file",
            "FunctionAgent": f"{base_url}/assistants/function"
        }

        return endpoints.get(agent_type)

    def _validate_step_result(self, result: Dict[str, Any], step: Dict[str, Any]) -> bool:
        """
        Validate a step execution result

        Args:
            result: Step execution result
            step: Step configuration

        Returns:
            True if result is valid
        """
        if not result:
            return False

        # Check for basic result structure
        if "text" not in result:
            return False

        # Check for error indicators
        if result.get("error") or result.get("success") == False:
            return False

        # Step-specific validation could be added here
        return True

    def _compile_results(self, task_id: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compile and format task execution results

        Args:
            task_id: Task identifier
            results: List of step results

        Returns:
            Compiled final result
        """
        successful_steps = [r for r in results if r.get("success", False)]
        failed_steps = [r for r in results if not r.get("success", False)]

        # Build response text
        response_text = f"Task completed with {len(successful_steps)} successful steps"

        if failed_steps:
            response_text += f" and {len(failed_steps)} failed steps"

        response_text += ":\n\n"

        # Add details for each step
        for result in results:
            step_num = result["step_number"]
            success = result.get("success", False)

            status_icon = "✅" if success else "❌"
            response_text += f"{status_icon} **Step {step_num}**: "

            if success:
                step_result = result.get("result", {})
                text = step_result.get("text", "Completed successfully")
                # Truncate long responses
                if len(text) > 200:
                    text = text[:200] + "..."
                response_text += f"{text}\n"
            else:
                error = result.get("error", "Unknown error")
                response_text += f"Failed - {error}\n"

        # Collect sources from all successful steps
        all_sources = []
        for result in successful_steps:
            step_result = result.get("result", {})
            sources = step_result.get("sources", [])
            all_sources.extend(sources)

        return {
            "text": response_text,
            "sources": all_sources[:10],  # Limit to 10 sources
            "successful_steps": len(successful_steps),
            "total_steps": len(results)
        }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a running task

        Args:
            task_id: Task identifier

        Returns:
            Task status information or None if not found
        """
        return self.active_tasks.get(task_id)

    def _call_assistant_api(self, endpoint: str, message: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Make a REST API call to an assistant endpoint

        Args:
            endpoint: API endpoint URL
            message: Message to send
            timeout: Request timeout in seconds

        Returns:
            API response data
        """
        try:
            payload = {
                "message": message,
                "context": {
                    "source": "TaskAssistant",
                    "timestamp": datetime.now().isoformat()
                }
            }

            response = requests.post(
                endpoint,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            response.raise_for_status()  # Raise exception for bad status codes

            result = response.json()

            if result.get("success"):
                return result.get("response", {})
            else:
                error_msg = result.get("error", "Unknown API error")
                logger.error(f"Assistant API returned error: {error_msg}")
                return {"error": error_msg}

        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling assistant API: {endpoint}")
            return {"error": f"Request timeout after {timeout} seconds"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling assistant API: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from assistant API: {str(e)}")
            return {"error": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error calling assistant API: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled
        """
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "cancelled"
            del self.active_tasks[task_id]
            return True
        return False