"""
Memory Repository Service

Handles persistent storage and retrieval of task results, embeddings, and learning data
using ChromaDB for embeddings and SQL database for metadata.
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

logger = logging.getLogger(__name__)

class MemoryRepository:
    """
    Repository for storing and retrieving task execution memory
    """

    def __init__(self, chroma_service=None, db_session=None):
        self.chroma_service = chroma_service
        self.db_session = db_session
        self.collection_name = "task_memory"

        # Initialize ChromaDB collection
        self._initialize_memory_collection()

    def _initialize_memory_collection(self):
        """Initialize the memory collection in ChromaDB"""
        try:
            if self.chroma_service and self.chroma_service.is_available():
                # Create collection if it doesn't exist
                collections = self.chroma_service.list_collections()
                if self.collection_name not in collections:
                    self.chroma_service.create_collection(self.collection_name)
                    logger.info(f"Created memory collection: {self.collection_name}")
                else:
                    logger.info(f"Memory collection already exists: {self.collection_name}")
            else:
                logger.warning("ChromaDB service not available for memory storage")
        except Exception as e:
            logger.error(f"Error initializing memory collection: {str(e)}")

    def store_task_result(self, task):
        """
        Store a completed task result in memory for future learning

        Args:
            task: Completed Task object
        """
        try:
            if not self.chroma_service or not self.chroma_service.is_available():
                logger.warning("ChromaDB not available, skipping memory storage")
                return

            # Create embedding from task data
            task_text = self._create_task_embedding_text(task)
            embedding = self._generate_embedding(task_text)

            # Create metadata
            metadata = self._create_task_metadata(task)

            # Store in ChromaDB
            doc_id = f"task_{task.id}"
            self.chroma_service.add_documents(
                collection_name=self.collection_name,
                documents=[task_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )

            # Store detailed result in SQL database if available
            if self.db_session:
                self._store_task_details_sql(task)

            logger.info(f"Stored task {task.id} in memory")

        except Exception as e:
            logger.error(f"Error storing task result: {str(e)}")

    def _create_task_embedding_text(self, task) -> str:
        """
        Create text representation for embedding from task data

        Args:
            task: Task object

        Returns:
            Text representation for embedding
        """
        text_parts = [
            f"Task: {task.message}",
            f"User: {task.user_id}",
            f"Status: {task.status.value}",
            f"Steps: {len(task.steps)}"
        ]

        # Add step information
        for i, step in enumerate(task.steps):
            text_parts.append(f"Step {i}: {step.type} - {step.status.value}")
            if step.result:
                text_parts.append(f"Result: {str(step.result)[:200]}")
            if step.error:
                text_parts.append(f"Error: {step.error}")

        return " | ".join(text_parts)

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # For now, create a simple hash-based embedding
        # In production, this would use a proper embedding model
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float list (simplified embedding)
        embedding = [float(b) / 255.0 for b in hash_bytes]

        # Pad to standard embedding size (384 for simplicity)
        while len(embedding) < 384:
            embedding.extend(embedding)

        return embedding[:384]

    def _create_task_metadata(self, task) -> Dict[str, Any]:
        """
        Create metadata for task storage

        Args:
            task: Task object

        Returns:
            Metadata dictionary
        """
        metadata = {
            'task_id': task.id,
            'user_id': task.user_id,
            'message': task.message,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'total_steps': len(task.steps),
            'successful_steps': sum(1 for s in task.steps if s.status.value == 'completed'),
            'failed_steps': sum(1 for s in task.steps if s.status.value == 'failed'),
            'session_id': task.session_id
        }

        # Add step details
        for i, step in enumerate(task.steps):
            metadata[f'step_{i}_type'] = step.type
            metadata[f'step_{i}_status'] = step.status.value
            metadata[f'step_{i}_strategy'] = step.strategy_used or 'default'
            metadata[f'step_{i}_execution_time'] = step.execution_time or 0

        return metadata

    def _store_task_details_sql(self, task):
        """
        Store detailed task information in SQL database

        Args:
            task: Task object
        """
        try:
            # This would store in a TaskMemory model
            # For now, we'll skip the SQL implementation
            # In production, this would create records in task_memory and task_steps tables
            pass
        except Exception as e:
            logger.error(f"Error storing task details in SQL: {str(e)}")

    def find_similar_tasks(self, query_task, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar tasks based on the query task

        Args:
            query_task: Task to find similar tasks for
            limit: Maximum number of similar tasks to return

        Returns:
            List of similar task metadata
        """
        try:
            if not self.chroma_service or not self.chroma_service.is_available():
                return []

            # Create query text from task
            query_text = self._create_task_embedding_text(query_task)
            query_embedding = self._generate_embedding(query_text)

            # Search for similar tasks
            results = self.chroma_service.query_documents(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=limit
            )

            if not results or 'metadatas' not in results:
                return []

            similar_tasks = []
            for metadata in results['metadatas'][0]:
                similar_tasks.append(metadata)

            logger.info(f"Found {len(similar_tasks)} similar tasks")
            return similar_tasks

        except Exception as e:
            logger.error(f"Error finding similar tasks: {str(e)}")
            return []

    def find_similar_steps(self, step, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar steps for strategy selection

        Args:
            step: TaskStep to find similar steps for
            limit: Maximum number of similar steps to return

        Returns:
            List of similar step metadata
        """
        try:
            if not self.chroma_service or not self.chroma_service.is_available():
                return []

            # Create query text from step
            query_text = f"Step type: {step.type} | Data: {json.dumps(step.data)}"
            query_embedding = self._generate_embedding(query_text)

            # Search for similar steps
            results = self.chroma_service.query_documents(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=limit * 2  # Get more to filter for steps
            )

            if not results or 'metadatas' not in results:
                return []

            similar_steps = []
            for metadata in results['metadatas'][0]:
                # Extract step information from metadata
                step_info = self._extract_step_info_from_metadata(metadata, step.type)
                if step_info:
                    similar_steps.append(step_info)

                if len(similar_steps) >= limit:
                    break

            logger.info(f"Found {len(similar_steps)} similar steps for type {step.type}")
            return similar_steps

        except Exception as e:
            logger.error(f"Error finding similar steps: {str(e)}")
            return []

    def _extract_step_info_from_metadata(self, metadata: Dict[str, Any], step_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract step information from task metadata

        Args:
            metadata: Task metadata
            step_type: Type of step to extract

        Returns:
            Step information dictionary
        """
        try:
            # Look for steps matching the requested type
            for i in range(metadata.get('total_steps', 0)):
                step_key_type = f'step_{i}_type'
                step_key_status = f'step_{i}_status'
                step_key_strategy = f'step_{i}_strategy'
                step_key_time = f'step_{i}_execution_time'

                if metadata.get(step_key_type) == step_type:
                    return {
                        'step_type': step_type,
                        'strategy_used': metadata.get(step_key_strategy, 'default'),
                        'execution_time': metadata.get(step_key_time, 0),
                        'success': metadata.get(step_key_status) == 'completed',
                        'task_id': metadata.get('task_id'),
                        'created_at': metadata.get('created_at')
                    }

            return None

        except Exception as e:
            logger.error(f"Error extracting step info: {str(e)}")
            return None

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored memory

        Returns:
            Memory statistics
        """
        try:
            if not self.chroma_service or not self.chroma_service.is_available():
                return {'error': 'ChromaDB not available'}

            stats = self.chroma_service.get_collection_stats(self.collection_name)

            if 'error' in stats:
                return stats

            return {
                'total_tasks': stats.get('count', 0),
                'collection_name': self.collection_name,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {'error': str(e)}

    def cleanup_old_memory(self, days_to_keep: int = 30):
        """
        Clean up old memory entries

        Args:
            days_to_keep: Number of days of memory to keep
        """
        try:
            if not self.chroma_service or not self.chroma_service.is_available():
                return

            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # This would require more complex filtering in ChromaDB
            # For now, we'll log the intent
            logger.info(f"Memory cleanup requested: keeping data from last {days_to_keep} days")

        except Exception as e:
            logger.error(f"Error during memory cleanup: {str(e)}")

    def optimize_memory(self):
        """
        Optimize memory storage and indexing
        """
        try:
            if not self.chroma_service or not self.chroma_service.is_available():
                return

            # This would involve rebuilding indexes, compacting storage, etc.
            logger.info("Memory optimization requested")

        except Exception as e:
            logger.error(f"Error during memory optimization: {str(e)}")
