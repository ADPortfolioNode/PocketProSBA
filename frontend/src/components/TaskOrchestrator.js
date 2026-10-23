import React, { useState, useRef } from 'react';
import { Card, Form, Button, Row, Col, Badge, ListGroup } from 'react-bootstrap';
import TaskProgress from './TaskProgress';
import apiClient from '../api/apiClient';
import LoadingBar from './LoadingBar';
import { ErrorState } from './AsyncState';
import { friendlyError } from '../utils/friendlyError';

const TaskOrchestrator = () => {
  const [taskMessage, setTaskMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [decomposedSteps, setDecomposedSteps] = useState([]);
  const [stepResults, setStepResults] = useState([]);
  const [validationResults, setValidationResults] = useState([]);
  const [error, setError] = useState(null);
  const [busyStep, setBusyStep] = useState(null); // e.g. 'Running step 2…'
  const retryRef = useRef(null); // re-runs whatever just failed
  const noEvent = { preventDefault() {} };

  // Step 1: Decompose task
  const handleDecompose = async (e) => {
    e.preventDefault();
    retryRef.current = null;
    if (!taskMessage.trim()) {
      setError('Please enter a task description');
      return;
    }
    setSubmitting(true);
    setError(null);
    setDecomposedSteps([]);
    setStepResults([]);
    setValidationResults([]);
    try {
      const message = taskMessage.trim();
      const sessionId = 'session_' + Date.now();
      // Prefer structured steps from decompose; also capture free-text response for UX.
      const res = await apiClient.post('/api/decompose', {
        message,
        session_id: sessionId
      });
      const payload = res?.data || res || {};
      const steps =
        payload.steps ||
        payload.response?.steps ||
        [];
      setDecomposedSteps(Array.isArray(steps) ? steps : []);
      // Soft-run orchestrator so Tasks tab also exercises the production path
      try {
        await apiClient.post('/api/orchestrator/submit', {
          message,
          user_id: '1',
          session_id: sessionId,
        });
      } catch (orchErr) {
        console.warn('Orchestrator submit optional path failed:', orchErr);
      }
      setTaskMessage('');
    } catch (err) {
      retryRef.current = () => handleDecompose(noEvent);
      setError(friendlyError(err, "We couldn't break that task into steps. Please try again."));
      console.error('Decompose error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Step 2: Execute each decomposed step
  const handleExecuteStep = async (step, idx) => {
    setBusyStep(`Running step ${idx + 1}…`);
    setError(null);
    try {
      const res = await apiClient.post('/api/execute', { task: step });
      setStepResults(prev => {
        const updated = [...prev];
        updated[idx] = res?.data ?? res; // axios response -> JSON body
        return updated;
      });
    } catch (err) {
      retryRef.current = () => handleExecuteStep(step, idx);
      setError(friendlyError(err, "That step didn't run. Please try again."));
      console.error('Execute step error:', err);
    } finally {
      setBusyStep(null);
    }
  };

  // Step 3: Validate step result
  const handleValidateStep = async (result, step, idx) => {
    setBusyStep(`Checking step ${idx + 1}…`);
    setError(null);
    try {
      const res = await apiClient.post('/api/validate', { result, task: step });
      setValidationResults(prev => {
        const updated = [...prev];
        updated[idx] = res?.data ?? res; // axios response -> JSON body
        return updated;
      });
    } catch (err) {
      retryRef.current = () => handleValidateStep(result, step, idx);
      setError(friendlyError(err, "We couldn't check that result. Please try again."));
      console.error('Validate step error:', err);
    } finally {
      setBusyStep(null);
    }
  };

  return (
    <div className="task-orchestrator">
      <Card className="mb-4">
        <Card.Header>
          <h4 className="mb-0">🤖 Self-Optimizing Task Orchestrator</h4>
        </Card.Header>
        <Card.Body>
          <p className="text-muted">
            Submit complex tasks and let our AI system automatically decompose, execute, and optimize
            the process using machine learning and feedback loops.
          </p>

          <Form onSubmit={handleDecompose}>
            <Form.Group className="mb-3">
              <Form.Label>Task Description</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="Describe your task in detail (e.g., 'Help me find SBA loan options for my small business and compare interest rates')"
                value={taskMessage}
                onChange={(e) => setTaskMessage(e.target.value)}
                disabled={submitting}
              />
              <Form.Text className="text-muted">
                Be specific about what you want to accomplish. The system will automatically break it down into steps.
              </Form.Text>
            </Form.Group>
            <Button
              type="submit"
              variant="primary"
              disabled={submitting || !taskMessage.trim()}
              className="w-100"
            >
              {submitting ? <LoadingBar inline label="Decomposing task…" /> : 'Decompose Task'}
            </Button>
          </Form>

          {submitting && <LoadingBar label="Breaking your task into steps…" className="py-3" />}
          {busyStep && <LoadingBar label={busyStep} className="py-3" />}
          {error && !submitting && (
            <ErrorState
              compact
              title="That didn't finish"
              message={error}
              onRetry={() => { const again = retryRef.current; setError(null); if (again) again(); }}
              retryLabel={retryRef.current ? 'Retry' : 'OK'}
            />
          )}

          {decomposedSteps.length > 0 && (
            <div className="mt-4">
              <h5>Decomposed Steps</h5>
              <ListGroup>
                {decomposedSteps.map((step, idx) => (
                  <ListGroup.Item key={idx}>
                    {step.instruction || step}
                    <Button className="ms-2" size="sm" variant="info" onClick={() => handleExecuteStep(step, idx)}>
                      Execute
                    </Button>
                    {stepResults[idx] && (
                      <span className="ms-2">Result: {stepResults[idx].result}</span>
                    )}
                    {stepResults[idx] && (
                      <Button className="ms-2" size="sm" variant="success" onClick={() => handleValidateStep(stepResults[idx].result, step, idx)}>
                        Validate
                      </Button>
                    )}
                    {validationResults[idx] && (
                      <span className="ms-2">Validation: {validationResults[idx].status}</span>
                    )}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </div>
          )}
        </Card.Body>
      </Card>

      <Card className="mb-4">
        <Card.Header>
          <h5 className="mb-0">How It Works</h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={4} className="text-center mb-3">
              <div className="h3 mb-2">📝</div>
              <h6>1. Task Analysis</h6>
              <small className="text-muted">
                AI analyzes your request and breaks it down into executable steps
              </small>
            </Col>
            <Col md={4} className="text-center mb-3">
              <div className="h3 mb-2">⚡</div>
              <h6>2. Smart Execution</h6>
              <small className="text-muted">
                System selects optimal strategies and executes steps with feedback loops
              </small>
            </Col>
            <Col md={4} className="text-center mb-3">
              <div className="h3 mb-2">🧠</div>
              <h6>3. Learning & Optimization</h6>
              <small className="text-muted">
                Results are stored in memory for continuous improvement
              </small>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </div>
  );
};

export default TaskOrchestrator;
