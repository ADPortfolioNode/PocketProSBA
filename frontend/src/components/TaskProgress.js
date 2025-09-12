import React, { useState, useEffect } from 'react';
import { Card, ProgressBar, Badge, Button, Alert, Spinner } from 'react-bootstrap';
import apiClient from '../api/apiClient';

const TaskProgress = ({ taskId, onTaskComplete, onTaskError }) => {
  const [taskStatus, setTaskStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);

  useEffect(() => {
    if (taskId) {
      fetchTaskStatus();
      // Start polling for updates
      const interval = setInterval(fetchTaskStatus, 2000); // Poll every 2 seconds
      setPollingInterval(interval);
    }

    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [taskId]);

  const fetchTaskStatus = async () => {
    try {
      const response = await apiClient.get(`/orchestrator/task/${taskId}`);
      const status = response.data;

      setTaskStatus(status);
      setLoading(false);
      setError(null);

      // Check if task is complete
      if (status.status === 'completed') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        if (onTaskComplete) {
          onTaskComplete(status);
        }
      } else if (status.status === 'failed') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        if (onTaskError) {
          onTaskError(status);
        }
      }
    } catch (err) {
      setError('Failed to fetch task status');
      setLoading(false);
      console.error('Error fetching task status:', err);
    }
  };

  const getStatusVariant = (status) => {
    switch (status) {
      case 'pending': return 'secondary';
      case 'decomposing': return 'info';
      case 'executing': return 'primary';
      case 'validating': return 'warning';
      case 'completed': return 'success';
      case 'failed': return 'danger';
      case 'retrying': return 'warning';
      default: return 'secondary';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return 'Task Submitted';
      case 'decomposing': return 'Analyzing Request';
      case 'executing': return 'Executing Steps';
      case 'validating': return 'Validating Results';
      case 'completed': return 'Task Completed';
      case 'failed': return 'Task Failed';
      case 'retrying': return 'Retrying Failed Steps';
      default: return status;
    }
  };

  if (loading) {
    return (
      <Card className="mb-3">
        <Card.Body className="text-center">
          <Spinner animation="border" />
          <p className="mt-2">Loading task status...</p>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="danger" className="mb-3">
        <Alert.Heading>Task Status Error</Alert.Heading>
        <p>{error}</p>
        <Button variant="outline-danger" onClick={fetchTaskStatus}>
          Retry
        </Button>
      </Alert>
    );
  }

  if (!taskStatus) {
    return null;
  }

  return (
    <Card className="mb-3">
      <Card.Header>
        <div className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Task Progress</h5>
          <Badge bg={getStatusVariant(taskStatus.status)}>
            {getStatusText(taskStatus.status)}
          </Badge>
        </div>
      </Card.Header>
      <Card.Body>
        <div className="mb-3">
          <div className="d-flex justify-content-between mb-1">
            <small>Progress</small>
            <small>{taskStatus.progress?.toFixed(1) || 0}%</small>
          </div>
          <ProgressBar
            now={taskStatus.progress || 0}
            variant={getStatusVariant(taskStatus.status)}
            animated={taskStatus.status === 'executing' || taskStatus.status === 'decomposing'}
          />
        </div>

        <div className="row text-center">
          <div className="col-6">
            <div className="h4 mb-0">{taskStatus.current_step || 0}</div>
            <small className="text-muted">Current Step</small>
          </div>
          <div className="col-6">
            <div className="h4 mb-0">{taskStatus.total_steps || 0}</div>
            <small className="text-muted">Total Steps</small>
          </div>
        </div>

        {taskStatus.status === 'failed' && (
          <Alert variant="danger" className="mt-3">
            <small>Task execution failed. The system will attempt to retry with alternative strategies.</small>
          </Alert>
        )}

        {taskStatus.status === 'completed' && (
          <Alert variant="success" className="mt-3">
            <small>Task completed successfully! Results are ready.</small>
          </Alert>
        )}
      </Card.Body>
    </Card>
  );
};

export default TaskProgress;
