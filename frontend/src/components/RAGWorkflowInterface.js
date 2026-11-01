import React, { useState } from 'react';
import { Card, Button, Form, ListGroup, Badge, Alert, ProgressBar } from 'react-bootstrap';
import apiClient, { handleUnauthorized } from '../api/apiClient';
import { authHeaders } from '../utils/authStorage';
import LoadingBar from './LoadingBar';
import { ErrorState } from './AsyncState';
import { friendlyError } from '../utils/friendlyError';
import { formatMagazineHtml } from '../utils/magazineProse';
import RagProcessPanel, { dedupeSources, extraLinksFromContent } from './RagProcessPanel';

// apiClient resolves to an axios response; the JSON body lives in .data.
const bodyOf = (res) => (res && res.data !== undefined ? res.data : res) || {};

const RAGWorkflowInterface = ({
  onSearch,
  onUpload,
  onRagQuery,
  documents,
  searchResults,
  ragResponse,
  chatMessages = [],
  chatPending = false,
  onChatSend,
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
  // Concierge chat on this page (same path + conversation as the Chat tab).
  const [chatInput, setChatInput] = useState('');
  const [ragChatSending, setRagChatSending] = useState(false);
  const [processQuery, setProcessQuery] = useState('');
  const [processStage, setProcessStage] = useState('idle');
  const [processSources, setProcessSources] = useState([]);
  const [processError, setProcessError] = useState(null);
  const [lastUpload, setLastUpload] = useState(null);

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

  // Send through the app's existing concierge path (MainLayout's
  // handleChatSend -> POST /api/chat). The process panel tracks the
  // stages around that single request and reports the sources the
  // answer actually used; the bubble itself carries only the message.
  const handleRagChatSend = async (e) => {
    if (e) e.preventDefault();
    const text = chatInput.trim();
    if (!text || ragChatSending) return;
    if (typeof onChatSend !== 'function') {
      setProcessStage('failed');
      setProcessError('Chat is not connected on this page. Open the Chat tab to ask the concierge.');
      return;
    }
    setProcessQuery(text);
    setProcessStage('retrieving');
    setProcessError(null);
    setRagChatSending(true);
    try {
      const response = await onChatSend(text);
      setProcessSources((response && response.sources) || []);
      setProcessStage('answered');
      setChatInput('');
    } catch (err) {
      setProcessStage('failed');
      setProcessError(friendlyError(err, "Your message didn't go through. Please try again."));
    } finally {
      setRagChatSending(false);
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
      let uploadResult = null;
      if (typeof onUpload === 'function') {
        uploadResult = await onUpload(selectedFile);
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
        uploadResult = await res.json();
      }
      setUploadProgress(100);
      // Upload -> immediately askable: surface the upload in the chat
      // section and prefill a question about it (only if the composer
      // is empty, so a draft is never clobbered).
      {
        const doc = (uploadResult && (uploadResult.document || uploadResult.file)) || null;
        const uploadedName = (doc && doc.filename) || (uploadResult && uploadResult.filename) || selectedFile.name;
        setLastUpload({
          filename: uploadedName,
          chunks: doc ? doc.chunks : undefined,
          ragStatus: (uploadResult && uploadResult.rag_status) || (doc && doc.rag_status) || undefined,
        });
        setChatInput((prev) => (prev.trim() ? prev : `Tell me about my uploaded document "${uploadedName}".`));
      }
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

  const ragChatThinking = chatPending || ragChatSending;

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
      {/* Concierge chat on the RAG page: same concierge path and same
          conversation as the Chat tab (props from MainLayout). The bubble
          carries only the conversational message; sources live in the
          RAG process panel and the Links & resources list below. */}
      <Card className="mb-3" data-testid="rag-concierge-chat">
        <Card.Header>
          <h5 className="mb-0">Chat with your documents</h5>
        </Card.Header>
        <Card.Body>
          <p className="text-muted">
            Ask the concierge here — it searches your uploaded documents and
            SBA resources, just like the Chat tab, and your conversation is
            shared with the Chat tab.
          </p>
          {lastUpload && (
            <Alert variant="success">
              Uploaded “{lastUpload.filename}”
              {lastUpload.chunks !== undefined && ` · ${lastUpload.chunks} chunk(s)`}
              {lastUpload.ragStatus && ` · RAG: ${lastUpload.ragStatus}`} — you can
              ask about it below without leaving this page.
            </Alert>
          )}
          <div role="log" aria-label="RAG chat conversation" className="mb-3">
            {chatMessages.length === 0 && !ragChatThinking && (
              <p className="text-muted">No messages yet. Ask about a document you uploaded, or about SBA programs.</p>
            )}
            {chatMessages.map((message, index) => (
              <div key={message.id || index} className="mb-2">
                <strong>{message.role === 'user' ? 'You' : 'Assistant'}: </strong>
                <span dangerouslySetInnerHTML={{ __html: formatMagazineHtml(typeof message.content === 'string' ? message.content : String(message.content ?? '')) }} />
              </div>
            ))}
            {ragChatThinking && <p className="text-muted">Concierge is thinking…</p>}
          </div>
          {processStage === 'failed' && processError && (
            <Alert variant="danger" role="alert">{processError}</Alert>
          )}
          <Form onSubmit={handleRagChatSend}>
            <Form.Group controlId="ragChatInput" className="mb-3">
              <Form.Label>Ask the concierge</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="Ask about your documents or SBA programs…"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
              />
            </Form.Group>
            <Button variant="primary" type="submit" disabled={!chatInput.trim() || ragChatThinking || typeof onChatSend !== 'function'}>
              Send
            </Button>
            {typeof onChatSend !== 'function' && (
              <p className="text-muted mt-2 mb-0">Chat connects through the concierge when this page is opened in the app.</p>
            )}
          </Form>
          {(() => {
            const shown = dedupeSources(processSources);
            const lastAssistant = [...chatMessages].reverse().find((m) => m.role !== 'user');
            const more = extraLinksFromContent(lastAssistant ? lastAssistant.content : '', shown);
            if (shown.length === 0 && more.length === 0) return null;
            return (
              <div className="mt-3">
                <h6>Links &amp; resources</h6>
                <ListGroup>
                  {shown.map((source) => (
                    <ListGroup.Item key={source.href || source.label}>
                      {source.href ? <a href={source.href}>{source.label}</a> : source.label}
                    </ListGroup.Item>
                  ))}
                </ListGroup>
                {more.length > 0 && (
                  <div className="mt-2">
                    <h6>More links</h6>
                    <ListGroup>
                      {more.map((link) => (
                        <ListGroup.Item key={link.href}>
                          <a href={link.href}>{link.label}</a>
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </div>
                )}
              </div>
            );
          })()}
        </Card.Body>
      </Card>
      <RagProcessPanel query={processQuery} stage={processStage} sources={processSources} error={processError} />
      {stepContent}
    </div>
  );
};

export default RAGWorkflowInterface;
