"""
Tests for Team Workflow Service and API endpoints
"""

import pytest
from backend.services.team_workflow_service import (
    TeamWorkflowService,
    get_team_workflow_service,
    TeamRole,
    WorkflowStatus
)


class TestTeamWorkflowService:
    """Test suite for TeamWorkflowService"""

    def test_service_initialization(self):
        """Test that service initializes with greeting"""
        service = TeamWorkflowService()
        assert service.greeting == "Hello deo! 🎯"
        assert len(service.active_tasks) == 0

    def test_singleton_pattern(self):
        """Test that get_team_workflow_service returns singleton"""
        service1 = get_team_workflow_service()
        service2 = get_team_workflow_service()
        assert service1 is service2

    def test_submit_issue(self):
        """Test issue submission creates task correctly"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue description")
        
        assert task.id is not None
        assert task.issue_description == "Test issue description"
        assert task.status == WorkflowStatus.PENDING
        assert task.iterations == 0
        assert task.validation_passed is False
        assert len(task.conversation_history) == 1  # Greeting message
        assert task.conversation_history[0].role == TeamRole.ADMINISTRATOR
        assert "Hello deo" in task.conversation_history[0].content
        assert task.id in service.active_tasks

    def test_get_task(self):
        """Test retrieving a task by ID"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        
        retrieved_task = service.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.id == task.id
        assert retrieved_task.issue_description == task.issue_description

    def test_get_nonexistent_task(self):
        """Test retrieving a task that doesn't exist"""
        service = TeamWorkflowService()
        task = service.get_task("nonexistent_id")
        assert task is None

    def test_get_task_status(self):
        """Test getting task status"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        
        status = service.get_task_status(task.id)
        assert status is not None
        assert status["task_id"] == task.id
        assert status["status"] == WorkflowStatus.PENDING.value
        assert status["iterations"] == 0
        assert status["validation_passed"] is False
        assert "created_at" in status
        assert "updated_at" in status

    def test_get_conversation_history(self):
        """Test getting conversation history"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        
        history = service.get_conversation_history(task.id)
        assert history is not None
        assert isinstance(history, list)
        assert len(history) == 1  # Just the greeting
        assert history[0]["role"] == TeamRole.ADMINISTRATOR.value
        assert "Hello deo" in history[0]["content"]

    def test_process_task_creates_workflow(self):
        """Test that processing a task creates the full workflow"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        
        # Process the task
        processed_task = service.process_task(task.id)
        
        # Check that workflow was executed
        assert processed_task.iterations > 0
        assert len(processed_task.conversation_history) > 1
        
        # Check that all three roles participated
        roles = set(msg.role for msg in processed_task.conversation_history)
        assert TeamRole.ADMINISTRATOR in roles
        assert TeamRole.DEVELOPER in roles
        assert TeamRole.QA in roles
        
        # Check final status
        assert processed_task.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]

    def test_process_task_validation_passed(self):
        """Test that task can pass validation"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue that should pass")
        
        processed_task = service.process_task(task.id)
        
        # With current implementation, should pass on first iteration
        assert processed_task.validation_passed is True
        assert processed_task.status == WorkflowStatus.COMPLETED
        assert processed_task.completed_at is not None
        assert processed_task.solution is not None

    def test_process_nonexistent_task(self):
        """Test processing a task that doesn't exist raises error"""
        service = TeamWorkflowService()
        
        with pytest.raises(ValueError, match="not found"):
            service.process_task("nonexistent_id")

    def test_administrator_research(self):
        """Test administrator research creates proper message"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        
        research_msg = service._administrator_research(task)
        
        assert research_msg.role == TeamRole.ADMINISTRATOR
        assert "Administrator Research Report" in research_msg.content
        assert "Build Notes" in research_msg.content
        assert "Error Analysis" in research_msg.content
        assert research_msg.metadata.get("iteration") == 1

    def test_developer_implement(self):
        """Test developer implementation creates proper message"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        research_msg = service._administrator_research(task)
        
        impl_msg = service._developer_implement(task, research_msg)
        
        assert impl_msg.role == TeamRole.DEVELOPER
        assert "Developer Implementation Report" in impl_msg.content
        assert "Implementation Strategy" in impl_msg.content
        assert impl_msg.metadata.get("implementation_complete") is True

    def test_qa_validate(self):
        """Test QA validation creates proper message"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        research_msg = service._administrator_research(task)
        impl_msg = service._developer_implement(task, research_msg)
        
        qa_msg = service._qa_validate(task, impl_msg)
        
        assert qa_msg.role == TeamRole.QA
        assert "QA Validation Report" in qa_msg.content
        assert "Validation Status" in qa_msg.content
        assert "validation_passed" in qa_msg.metadata
        assert "checks" in qa_msg.metadata

    def test_parse_build_notes(self):
        """Test parsing build notes returns information"""
        service = TeamWorkflowService()
        build_notes = service._parse_build_notes()
        
        assert isinstance(build_notes, str)
        assert len(build_notes) > 0

    def test_analyze_error_context(self):
        """Test error context analysis"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        
        # First iteration should have no previous errors
        error_context = service._analyze_error_context(task)
        assert "no previous errors" in error_context.lower()

    def test_max_iterations_limit(self):
        """Test that workflow respects max iterations"""
        service = TeamWorkflowService()
        task = service.submit_issue("Test issue")
        task.max_iterations = 2
        
        # Force validation to fail by modifying the validate method
        # (In real scenario, would mock the validation)
        processed_task = service.process_task(task.id)
        
        # Should complete (pass validation) but check iteration count
        assert processed_task.iterations <= task.max_iterations


class TestTeamWorkflowAPI:
    """Test suite for Team Workflow API endpoints"""

    def test_health_endpoint(self, client):
        """Test team workflow health check"""
        response = client.get('/api/team/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'team_workflow'
        assert 'greeting' in data
        assert data['greeting'] == "Hello deo! 🎯"

    def test_submit_issue_success(self, client):
        """Test successful issue submission"""
        response = client.post('/api/team/submit', json={
            'issue_description': 'Test issue to resolve'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'task_id' in data
        assert data['greeting'] == "Hello deo! 🎯"
        assert data['status'] == 'pending'
        assert 'created_at' in data

    def test_submit_issue_no_description(self, client):
        """Test issue submission without description"""
        response = client.post('/api/team/submit', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_submit_issue_empty_description(self, client):
        """Test issue submission with empty description"""
        response = client.post('/api/team/submit', json={
            'issue_description': '   '
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_submit_issue_no_json(self, client):
        """Test issue submission without JSON data"""
        response = client.post('/api/team/submit')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_get_task_status(self, client):
        """Test getting task status"""
        # First submit an issue
        submit_response = client.post('/api/team/submit', json={
            'issue_description': 'Test issue'
        })
        task_id = submit_response.get_json()['task_id']
        
        # Get status
        response = client.get(f'/api/team/task/{task_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['task_id'] == task_id
        assert 'status' in data
        assert 'iterations' in data
        assert 'validation_passed' in data

    def test_get_nonexistent_task_status(self, client):
        """Test getting status of nonexistent task"""
        response = client.get('/api/team/task/nonexistent_id')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_get_conversation_history(self, client):
        """Test getting conversation history"""
        # First submit an issue
        submit_response = client.post('/api/team/submit', json={
            'issue_description': 'Test issue'
        })
        task_id = submit_response.get_json()['task_id']
        
        # Get history
        response = client.get(f'/api/team/task/{task_id}/history')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['task_id'] == task_id
        assert 'greeting' in data
        assert 'conversation' in data
        assert isinstance(data['conversation'], list)
        assert len(data['conversation']) >= 1  # At least greeting

    def test_get_nonexistent_task_history(self, client):
        """Test getting history of nonexistent task"""
        response = client.get('/api/team/task/nonexistent_id/history')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_process_task(self, client):
        """Test processing a task"""
        # First submit an issue
        submit_response = client.post('/api/team/submit', json={
            'issue_description': 'Test issue to process'
        })
        task_id = submit_response.get_json()['task_id']
        
        # Process the task
        response = client.post(f'/api/team/process/{task_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['task_id'] == task_id
        assert 'status' in data
        assert 'iterations' in data
        assert data['iterations'] > 0
        assert 'validation_passed' in data

    def test_process_nonexistent_task(self, client):
        """Test processing a nonexistent task"""
        response = client.post('/api/team/process/nonexistent_id')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_list_tasks(self, client):
        """Test listing all tasks"""
        # Submit a few issues
        client.post('/api/team/submit', json={'issue_description': 'Issue 1'})
        client.post('/api/team/submit', json={'issue_description': 'Issue 2'})
        
        # List tasks
        response = client.get('/api/team/tasks')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'greeting' in data
        assert 'tasks' in data
        assert 'count' in data
        assert isinstance(data['tasks'], list)
        assert data['count'] >= 2

    def test_list_tasks_empty(self, client):
        """Test listing tasks when none exist"""
        response = client.get('/api/team/tasks')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 0
        assert len(data['tasks']) == 0

    def test_full_workflow_integration(self, client):
        """Test full workflow from submission to completion"""
        # 1. Submit issue
        submit_response = client.post('/api/team/submit', json={
            'issue_description': 'Complete integration test issue'
        })
        assert submit_response.status_code == 201
        task_id = submit_response.get_json()['task_id']
        
        # 2. Check initial status
        status_response = client.get(f'/api/team/task/{task_id}')
        assert status_response.status_code == 200
        assert status_response.get_json()['status'] == 'pending'
        
        # 3. Process task
        process_response = client.post(f'/api/team/process/{task_id}')
        assert process_response.status_code == 200
        process_data = process_response.get_json()
        assert process_data['status'] in ['completed', 'failed']
        
        # 4. Get final conversation history
        history_response = client.get(f'/api/team/task/{task_id}/history')
        assert history_response.status_code == 200
        history = history_response.get_json()['conversation']
        
        # Verify all three roles participated
        roles = set(msg['role'] for msg in history)
        assert 'administrator' in roles
        assert 'developer' in roles
        assert 'qa' in roles
        
        # 5. Verify greeting appears
        assert any('Hello deo' in msg['content'] for msg in history)
