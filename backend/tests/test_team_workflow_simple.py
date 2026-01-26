"""
Simple standalone test for Team Workflow Service
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.team_workflow_service import TeamWorkflowService, TeamRole, WorkflowStatus


def test_service_initialization():
    """Test that service initializes with greeting"""
    print("Testing service initialization...")
    service = TeamWorkflowService()
    assert service.greeting == "Hello deo! 🎯", "Greeting doesn't match"
    assert len(service.active_tasks) == 0, "Should start with no tasks"
    print("✓ Service initialization passed")


def test_submit_issue():
    """Test issue submission creates task correctly"""
    print("\nTesting issue submission...")
    service = TeamWorkflowService()
    task = service.submit_issue("Test issue description")
    
    assert task.id is not None, "Task should have an ID"
    assert task.issue_description == "Test issue description", "Description doesn't match"
    assert task.status == WorkflowStatus.PENDING, "Initial status should be PENDING"
    assert task.iterations == 0, "Should start with 0 iterations"
    assert task.validation_passed is False, "Should not be validated initially"
    assert len(task.conversation_history) == 1, "Should have greeting message"
    assert task.conversation_history[0].role == TeamRole.ADMINISTRATOR, "First message should be from admin"
    assert "Hello deo" in task.conversation_history[0].content, "Greeting should contain 'Hello deo'"
    assert task.id in service.active_tasks, "Task should be in active tasks"
    print("✓ Issue submission passed")


def test_get_task():
    """Test retrieving a task by ID"""
    print("\nTesting task retrieval...")
    service = TeamWorkflowService()
    task = service.submit_issue("Test issue")
    
    retrieved_task = service.get_task(task.id)
    assert retrieved_task is not None, "Should retrieve the task"
    assert retrieved_task.id == task.id, "IDs should match"
    assert retrieved_task.issue_description == task.issue_description, "Descriptions should match"
    print("✓ Task retrieval passed")


def test_process_task():
    """Test that processing a task creates the full workflow"""
    print("\nTesting task processing...")
    service = TeamWorkflowService()
    task = service.submit_issue("Test issue for processing")
    
    # Process the task
    processed_task = service.process_task(task.id)
    
    # Check that workflow was executed
    assert processed_task.iterations > 0, "Should have at least one iteration"
    assert len(processed_task.conversation_history) > 1, "Should have multiple messages"
    
    # Check that all three roles participated
    roles = set(msg.role for msg in processed_task.conversation_history)
    assert TeamRole.ADMINISTRATOR in roles, "Administrator should participate"
    assert TeamRole.DEVELOPER in roles, "Developer should participate"
    assert TeamRole.QA in roles, "QA should participate"
    
    # Check final status
    assert processed_task.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED], \
        f"Final status should be COMPLETED or FAILED, got {processed_task.status}"
    
    print(f"✓ Task processing passed (Status: {processed_task.status.value}, Iterations: {processed_task.iterations})")


def test_greeting_message():
    """Test that greeting message appears correctly"""
    print("\nTesting greeting message...")
    service = TeamWorkflowService()
    assert service.greeting == "Hello deo! 🎯", "Service greeting should be correct"
    
    task = service.submit_issue("Test")
    history = service.get_conversation_history(task.id)
    
    greeting_found = False
    for msg in history:
        if "Hello deo" in msg["content"]:
            greeting_found = True
            break
    
    assert greeting_found, "Greeting should appear in conversation history"
    print("✓ Greeting message passed")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Team Workflow Service Tests")
    print("=" * 60)
    
    tests = [
        test_service_initialization,
        test_submit_issue,
        test_get_task,
        test_process_task,
        test_greeting_message
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
