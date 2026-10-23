import React, { useState } from 'react';
import { Card, Button, Form, ListGroup, Badge, Alert, ProgressBar } from 'react-bootstrap';
import apiClient, { handleUnauthorized } from '../api/apiClient';
import { authHeaders } from '../utils/authStorage';
import LoadingBar from './LoadingBar';
import { ErrorState } from './AsyncState';
import { friendlyError } from '../utils/friendlyError';

// apiClient resolves to an axios response; the JSON body lives in .data.
const bodyOf = (res) => (res && res.data !== undefined ? res.data : res) || {};

const RAGWorkflowInterface = ({ 
  onSearch, 
  onUpload, 
  onRagQuery, 
  documents,
  searchResults,
  ragResponse
}) => {
  const [currentStep, setCurrentStep] = useState('upload');
  const [queryText, setQueryText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [decomposedSteps, setDecomposedSteps] = useState([]);
  const [stepResults, setStepResults] = useState([]);
  const [validationResult, setValidationResult] = useState(null);
  const [queryResults, setQueryResults] = useState([]);
  const [finalResponse, setFinalResponse] = useState(null);
  // Shared pending/failure state for every backend step: a loader while the
  // request (and apiClient's retries) run, a friendly error with Retry after.
  const [busy, setBusy] = useState(null);
  const [failure, setFailure] = useState(null);

  const runStep = async (label, fn, retry) => {
    setBusy(label);
    setFailure(null);
    try {
      await fn();
    } catch (err) {
      console.error(`${label} failed:`, err);
      setFailure({ message: friendlyError(err), retry });
    } finally {
      setBusy(null);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploadProgress(0);
    const fakeProgress = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev == null || prev >= 90) {
          clearInterval(fakeProgress);
          return prev;
        }
        return prev + 10;
      });
    }, 300);
    try {
      if (typeof onUpload === 'function') {
        await onUpload(selectedFile);
      } else {
        // Direct upload when parent handler not provided
        const formData = new FormData();
        formData.append('file', selectedFile);
        // Raw fetch (multipart) bypasses apiClient: send the token ourselves.
        let res = await fetch('/api/files', { method: 'POST', headers: authHeaders(), body: formData });
        if (!res.ok && res.status !== 401) {
          res = await fetch('/api/documents/upload', { method: 'POST', headers: authHeaders(), body: formData });
        }
        if (res.status === 401 && typeof handleUnauthorized === 'function') {
          handleUnauthorized({ response: { status: 401 }, config: { url: '/api/files' } });
        }
        if (!res.ok) throw new Error(`Server responded with ${res.status}`);
        await res.json();
      }
      setUploadProgress(100);
      setCurrentStep('search');
    } catch (err) {
      console.error('File upload error:', err);
      setUploadProgress(null);
      setFailure({ message: friendlyError(err, "The upload didn't finish. Please try again."), retry: handleUpload });
    } finally {
      clearInterval(fakeProgress);
      setTimeout(() => setUploadProgress(null), 800);
    }
  };

  // Step 1: Decompose task
  const handleDecompose = (taskText) => runStep('Breaking your task into steps…', async () => {
    const res = await apiClient.post('/api/decompose', {
      message: taskText,
      session_id: 'session_' + Date.now()
    });
    const body = bodyOf(res);
    setDecomposedSteps(body.response?.steps || body.steps || []);
    setCurrentStep('execute');
  }, () => handleDecompose(taskText));

  // Step 2: Execute each decomposed step
  const handleExecuteStep = (step) => runStep('Running this step…', async () => {
    const res = await apiClient.post('/api/execute', { task: step });
    setStepResults(prev => [...prev, bodyOf(res)]);
  }, () => handleExecuteStep(step));

  // Step 3: Validate step result
  const handleValidateStep = (result, step) => runStep('Checking the result…', async () => {
    const res = await apiClient.post('/api/validate', { result, task: step });
    setValidationResult(bodyOf(res));
  }, () => handleValidateStep(result, step));

  // Step 4: Query documents
  const handleQueryDocuments = (query) => runStep('Searching your documents…', async () => {
    const res = await apiClient.post('/api/query', { query, top_k: 5 });
    setQueryResults(bodyOf(res).results || []);
  }, () => handleQueryDocuments(query));

  // Step 5: Generate final response (simulate)
  const handleGenerateResponse = () => {
    setFinalResponse({ content: 'AI-generated answer based on validated steps and retrieved context.' });
    setCurrentStep('generate');
  };
              
  // Render step content based on currentStep
  let stepContent = null;
  switch (currentStep) {
    case 'upload':
      stepContent = (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">Upload Document</h5>
          </Card.Header>
          <Card.Body>
            <Form.Group controlId="uploadInput" className="mb-3">
              <Form.Label>Select a file to upload</Form.Label>
              <Form.Control type="file" onChange={handleFileSelect} />
            </Form.Group>
            <Button variant="primary" onClick={handleUpload} disabled={!selectedFile}>
              Upload
            </Button>
            <Button variant="secondary" className="ms-2" onClick={() => setCurrentStep('decompose')}>
              Start Task Without Upload
            </Button>
            {uploadProgress !== null && <ProgressBar now={uploadProgress} label={`${uploadProgress}%`} className="mt-3" />}
          </Card.Body>
        </Card>
      );
      break;
    case 'decompose':
      stepContent = (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">Decompose Task</h5>
          </Card.Header>
          <Card.Body>
            <Form onSubmit={e => { e.preventDefault(); handleDecompose(queryText); }}>
              <Form.Group controlId="decomposeInput" className="mb-3">
                <Form.Label>Describe your task</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  placeholder="e.g., Find SBA loan options and compare rates"
                  value={queryText}
                  onChange={e => setQueryText(e.target.value)}
                />
              </Form.Group>
              <Button variant="primary" type="submit" disabled={!queryText.trim()}>
                Decompose Task
              </Button>
            </Form>
            {decomposedSteps.length > 0 && (
              <ListGroup className="mt-4">
                {decomposedSteps.map((step, idx) => (
                  <ListGroup.Item key={idx}>{step.instruction || step}</ListGroup.Item>
                ))}
              </ListGroup>
            )}
            <Button className="mt-3" variant="success" onClick={() => setCurrentStep('execute')} disabled={decomposedSteps.length === 0}>
              Execute Steps
            </Button>
          </Card.Body>
        </Card>
      );
      break;
    case 'execute':
      stepContent = (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">Execute Steps</h5>
          </Card.Header>
          <Card.Body>
            {decomposedSteps.map((step, idx) => (
              <Button key={idx} className="mb-2" onClick={() => handleExecuteStep(step)}>
                Execute Step {idx + 1}
              </Button>
            ))}
            <ListGroup className="mt-3">
              {stepResults.map((result, idx) => (
                <ListGroup.Item key={idx}>{result.result}</ListGroup.Item>
              ))}
            </ListGroup>
            <Button className="mt-3" variant="info" onClick={() => setCurrentStep('validate')} disabled={stepResults.length === 0}>
              Validate Steps
            </Button>
          </Card.Body>
        </Card>
      );
      break;
    case 'validate':
      stepContent = (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">Validate Step Results</h5>
          </Card.Header>
          <Card.Body>
            {stepResults.map((result, idx) => (
              <Button key={idx} className="mb-2" onClick={() => handleValidateStep(result.result, decomposedSteps[idx])}>
                Validate Step {idx + 1}
              </Button>
            ))}
            {validationResult && (
              <Alert variant={validationResult.status === 'PASS' ? 'success' : 'danger'} className="mt-3">
                {validationResult.feedback}
              </Alert>
            )}
            <Button className="mt-3" variant="primary" onClick={() => setCurrentStep('query')}>
              Query Documents
            </Button>
          </Card.Body>
        </Card>
      );
      break;
    case 'query':
      stepContent = (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">Query Documents</h5>
          </Card.Header>
          <Card.Body>
            <Form onSubmit={e => { e.preventDefault(); handleQueryDocuments(queryText); }}>
              <Form.Group controlId="queryInput" className="mb-3">
                <Form.Label>Your Question</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  placeholder="e.g., What types of SBA loans are available for small businesses?"
                  value={queryText}
                  onChange={e => setQueryText(e.target.value)}
                />
              </Form.Group>
              <Button variant="primary" type="submit" disabled={!queryText.trim()}>
                Search & Generate Answer
              </Button>
            </Form>
            <ListGroup className="mt-3">
              {queryResults.map((result, idx) => (
                <ListGroup.Item key={idx}>{result.content}</ListGroup.Item>
              ))}
            </ListGroup>
            <Button className="mt-3" variant="success" onClick={handleGenerateResponse} disabled={queryResults.length === 0}>
              Generate Final Answer
            </Button>
          </Card.Body>
        </Card>
      );
      break;
    case 'generate':
      stepContent = (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">Generated Response</h5>
          </Card.Header>
          <Card.Body>
            <p className="mb-3">
              Based on the retrieved context, here is the AI-generated answer to your query.
            </p>
            {finalResponse ? (
              <Card className="mb-4 bg-light">
                <Card.Body>
                  <Card.Title className="text-primary">Query</Card.Title>
                  <Card.Text className="mb-3">{queryText}</Card.Text>
                  <Card.Title className="text-primary">Response</Card.Title>
                  <Card.Text style={{ whiteSpace: 'pre-line' }}>{finalResponse.content}</Card.Text>
                </Card.Body>
              </Card>
            ) : (
              <Alert variant="info">
                No response generated yet. Submit a query to see results.
              </Alert>
            )}
            <Button className="mt-3" variant="primary" onClick={() => setCurrentStep('decompose')}>
              Start New Task
            </Button>
          </Card.Body>
        </Card>
      );
      break;
    default:
      stepContent = null;
  }

  return (
    <div>
      {Array.isArray(documents) && documents.length > 0 && (
        <div className="mt-3 mb-3">
          <h6>Available Documents</h6>
          <ListGroup>
            {documents.map((doc, index) => (
              <ListGroup.Item key={index} className="d-flex justify-content-between align-items-center">
                <div>
                  <strong>{doc.filename}</strong>
                  {doc.pages && <Badge bg="info" className="ms-2">{doc.pages} pages</Badge>}
                  <small className="d-block text-muted">
                    {doc.type && `Type: ${doc.type.toUpperCase()}`}
                    {doc.size && ` • Size: ${(doc.size / 1024).toFixed(1)} KB`}
                    {doc.modified && ` • Modified: ${doc.modified}`}
                  </small>
                </div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </div>
      )}
      {busy && <LoadingBar label={busy} className="py-3" />}
      {!busy && failure && (
        <ErrorState compact title="That step didn't finish" message={failure.message} onRetry={failure.retry} />
      )}
      {stepContent}
    </div>
  );
};

export default RAGWorkflowInterface;
