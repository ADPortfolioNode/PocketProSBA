import pytest
import tempfile
import os
import json
import time
import unittest.mock as mock
from services.memory_repository import MemoryRepository

class TestMemoryRepository:
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def mock_chroma_service(self):
        """Mock ChromaDB service"""
        return mock.MagicMock()

    @pytest.fixture
    def memory_repo(self, mock_chroma_service, temp_db_path):
        """Create test memory repository"""
        return MemoryRepository(mock_chroma_service, temp_db_path)

    def test_store_task_result(self, memory_repo):
        """Test storing task result"""
        task_id = "task_123"
        task_results = [{"step": 1, "result": "success"}]

        memory_repo.store_task_result(task_id, task_results)

        # Verify task was stored
        history = memory_repo.get_task_history(task_id)
        assert history is not None
        assert history["task"]["task_id"] == task_id
        assert json.loads(history["task"]["result"]) == task_results

    def test_store_step_result(self, memory_repo):
        """Test storing step result"""
        task_id = "task_123"
        step_index = 0
        step_type = "document_search"
        result = {"documents": ["doc1", "doc2"]}

        memory_repo.store_step_result(task_id, step_index, step_type, result)

        # Verify step was stored
        history = memory_repo.get_task_history(task_id)
        assert history is not None
        assert len(history["steps"]) == 1
        assert history["steps"][0]["step_index"] == step_index
        assert history["steps"][0]["step_type"] == step_type
        assert json.loads(history["steps"][0]["result"]) == result

    def test_log_step_attempts(self, memory_repo):
        """Test logging step attempts"""
        task_id = "task_123"
        step_index = 0
        step_type = "document_search"
        attempt_logs = [
            {"attempt": 1, "strategy": "fast_search", "success": False, "error": "timeout", "timestamp": time.time()},
            {"attempt": 2, "strategy": "detailed_search", "success": True, "error": "", "timestamp": time.time()}
        ]

        memory_repo.log_step_attempts(task_id, step_index, step_type, attempt_logs)

        # Verify attempts were logged
        history = memory_repo.get_task_history(task_id)
        assert history is not None
        assert len(history["attempts"]) == 2
        assert history["attempts"][0]["strategy"] == "fast_search"
        assert history["attempts"][0]["success"] is False
        assert history["attempts"][1]["strategy"] == "detailed_search"
        assert history["attempts"][1]["success"] is True

    def test_get_best_strategy(self, memory_repo):
        """Test getting best strategy"""
        # Log some attempts to build strategy scores
        attempt_logs = [
            {"attempt": 1, "strategy": "fast_search", "success": True, "error": "", "timestamp": time.time()},
            {"attempt": 2, "strategy": "fast_search", "success": True, "error": "", "timestamp": time.time()},
            {"attempt": 3, "strategy": "detailed_search", "success": False, "error": "timeout", "timestamp": time.time()}
        ]

        memory_repo.log_step_attempts("task_123", 0, "document_search", attempt_logs)

        best_strategy = memory_repo.get_best_strategy("document_search")
        assert best_strategy == "fast_search"

    def test_find_similar_tasks(self, memory_repo, mock_chroma_service):
        """Test finding similar tasks"""
        task_embedding = [0.1, 0.2, 0.3]
        mock_chroma_service.query_documents_by_embedding.return_value = {
            "documents": ["similar_task_1", "similar_task_2"]
        }

        similar_tasks = memory_repo.find_similar_tasks(task_embedding)

        assert similar_tasks == ["similar_task_1", "similar_task_2"]
        mock_chroma_service.query_documents_by_embedding.assert_called_once_with(task_embedding, n_results=5)

    def test_find_similar_tasks_error(self, memory_repo, mock_chroma_service):
        """Test finding similar tasks with error"""
        task_embedding = [0.1, 0.2, 0.3]
        mock_chroma_service.query_documents_by_embedding.return_value = {
            "error": "ChromaDB connection failed"
        }

        similar_tasks = memory_repo.find_similar_tasks(task_embedding)

        assert similar_tasks == []

    def test_store_task_embedding(self, memory_repo, mock_chroma_service):
        """Test storing task embedding"""
        task_id = "task_123"
        task_data = {"query": "test query"}
        embedding = [0.1, 0.2, 0.3]

        memory_repo.store_task_embedding(task_id, task_data, embedding)

        mock_chroma_service.add_documents.assert_called_once()
        call_args = mock_chroma_service.add_documents.call_args
        assert call_args[0][0] == [json.dumps(task_data)]
        assert call_args[0][2] == [embedding]

    def test_get_task_history_nonexistent(self, memory_repo):
        """Test getting history for nonexistent task"""
        history = memory_repo.get_task_history("nonexistent_task")
        assert history is None

    def test_get_metrics(self, memory_repo):
        """Test getting metrics"""
        # Store some test data
        memory_repo.store_task_result("task_1", [{"result": "success"}])
        memory_repo.store_task_result("task_2", [{"result": "success"}])
        memory_repo.store_task_result("task_3", [{"result": "failed"}])

        metrics = memory_repo.get_metrics()

        assert metrics["total_tasks"] == 3
        assert metrics["success_rate"] == 2/3
        assert "avg_retries" in metrics
        assert "avg_execution_time" in metrics

    def test_strategy_score_update(self, memory_repo):
        """Test strategy score updates"""
        # First attempt - success
        memory_repo._update_strategy_score("document_search", "fast_search", True)

        # Second attempt - success
        memory_repo._update_strategy_score("document_search", "fast_search", True)

        # Third attempt - failure
        memory_repo._update_strategy_score("document_search", "fast_search", False)

        best_strategy = memory_repo.get_best_strategy("document_search")
        assert best_strategy == "fast_search"

        # Verify the score is updated correctly
        cursor = memory_repo.conn.cursor()
        cursor.execute('SELECT score, attempts, successes FROM strategy_scores WHERE step_type = ? AND strategy = ?',
                      ("document_search", "fast_search"))
        row = cursor.fetchone()
        assert row[1] == 3  # attempts
        assert row[2] == 2  # successes
        assert row[0] > 0   # score should be positive
