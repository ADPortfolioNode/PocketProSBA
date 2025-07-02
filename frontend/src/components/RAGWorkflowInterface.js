import React, { useState } from 'react';
import RAGWorkflowVisualization from './RAGWorkflowVisualization';

const RAGWorkflowInterface = ({ 
  onSearch, 
  onUpload, 
  onQuery, 
  documents,
  searchResults,
  ragResponse
}) => {
  const [currentStep, setCurrentStep] = useState('upload');
  const [queryText, setQueryText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeDocument, setActiveDocument] = useState(null);
  
  const handleStepChange = (step) => {
    setCurrentStep(step);
  };
  
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };
  
  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile);
      setCurrentStep('index'); // Move to the next step
    }
  };
  
  const handleSearch = (e) => {
    e.preventDefault();
    if (queryText.trim()) {
      onSearch(queryText);
      setCurrentStep('retrieve'); // Move to the retrieval step
    }
  };
  
  const handleRagQuery = (e) => {
    e.preventDefault();
    if (queryText.trim()) {
      onQuery(queryText);
      setCurrentStep('generate'); // Move to the generation step
    }
  };

  return (
    <div className="rag-workflow-interface">
      <RAGWorkflowVisualization activeStep={currentStep} />
      
      <div className="workflow-steps-container">
        <div className={`workflow-step-content ${currentStep === 'upload' ? 'active' : ''}`}>
          <h3>Step 1: Document Upload</h3>
          <p>Upload documents to build your knowledge base.</p>
          
          <div className="file-upload-area">
            <input 
              type="file" 
              id="rag-file-upload" 
              className="file-input" 
              onChange={handleFileSelect}
            />
            <label htmlFor="rag-file-upload" className="file-upload-label">
              {selectedFile ? selectedFile.name : 'Choose a file'}
            </label>
            <button 
              className="upload-button" 
              disabled={!selectedFile}
              onClick={handleUpload}
            >
              Upload Document
            </button>
          </div>
          
          <div className="document-list">
            <h4>Your Documents ({documents.length})</h4>
            {documents.length > 0 ? (
              <ul className="document-items">
                {documents.slice(0, 5).map(doc => (
                  <li 
                    key={doc.id} 
                    className={`document-item ${activeDocument === doc.id ? 'active' : ''}`}
                    onClick={() => setActiveDocument(doc.id)}
                  >
                    <span className="document-name">{doc.filename || 'Unnamed document'}</span>
                    {doc.chunk_count && (
                      <span className="document-chunks">{doc.chunk_count} chunks</span>
                    )}
                  </li>
                ))}
                {documents.length > 5 && (
                  <li className="document-item more">
                    And {documents.length - 5} more...
                  </li>
                )}
              </ul>
            ) : (
              <p className="no-documents">No documents uploaded yet.</p>
            )}
          </div>
          
          <div className="step-actions">
            <button 
              className="next-step-button"
              onClick={() => handleStepChange('index')}
              disabled={documents.length === 0}
            >
              Next: Indexing
            </button>
          </div>
        </div>
        
        <div className={`workflow-step-content ${currentStep === 'index' ? 'active' : ''}`}>
          <h3>Step 2: Indexing</h3>
          <p>Your documents are processed and indexed for semantic search.</p>
          
          <div className="indexing-info">
            <div className="info-item">
              <span className="info-label">Documents:</span>
              <span className="info-value">{documents.length}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Total Chunks:</span>
              <span className="info-value">
                {documents.reduce((sum, doc) => sum + (doc.chunk_count || 0), 0)}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Embedding Model:</span>
              <span className="info-value">OpenAI Embeddings</span>
            </div>
          </div>
          
          <div className="step-actions">
            <button 
              className="prev-step-button"
              onClick={() => handleStepChange('upload')}
            >
              Back: Upload
            </button>
            <button 
              className="next-step-button"
              onClick={() => handleStepChange('query')}
            >
              Next: Query
            </button>
          </div>
        </div>
        
        <div className={`workflow-step-content ${currentStep === 'query' ? 'active' : ''}`}>
          <h3>Step 3: Query</h3>
          <p>Ask questions about your documents.</p>
          
          <form className="query-form" onSubmit={handleSearch}>
            <input
              type="text"
              className="query-input"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="What would you like to know about your documents?"
            />
            <div className="query-actions">
              <button type="submit" className="search-button">
                Search
              </button>
              <button 
                type="button" 
                className="rag-button"
                onClick={handleRagQuery}
              >
                Generate Answer
              </button>
            </div>
          </form>
          
          <div className="step-actions">
            <button 
              className="prev-step-button"
              onClick={() => handleStepChange('index')}
            >
              Back: Indexing
            </button>
          </div>
        </div>
        
        <div className={`workflow-step-content ${currentStep === 'retrieve' ? 'active' : ''}`}>
          <h3>Step 4: Retrieval</h3>
          <p>Relevant context is retrieved from your documents.</p>
          
          <div className="retrieval-results">
            <h4>Search Results for: "{queryText}"</h4>
            
            {searchResults.length > 0 ? (
              <div className="results-list">
                {searchResults.map((result, index) => (
                  <div className="result-item" key={index}>
                    <div className="result-header">
                      <span className="result-source">
                        {result.metadata?.filename || 'Unknown source'}
                      </span>
                      {result.score && (
                        <span className="result-score">
                          Score: {Number(result.score).toFixed(2)}
                        </span>
                      )}
                    </div>
                    <div className="result-content">
                      {result.content || result.text || 'No content'}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-results">No results found. Try a different query.</p>
            )}
          </div>
          
          <div className="step-actions">
            <button 
              className="prev-step-button"
              onClick={() => handleStepChange('query')}
            >
              Back: Query
            </button>
            <button 
              className="next-step-button"
              onClick={() => {
                handleRagQuery({ preventDefault: () => {} });
              }}
              disabled={searchResults.length === 0}
            >
              Next: Generate Answer
            </button>
          </div>
        </div>
        
        <div className={`workflow-step-content ${currentStep === 'generate' ? 'active' : ''}`}>
          <h3>Step 5: Generation</h3>
          <p>The AI generates an answer based on the retrieved context.</p>
          
          {ragResponse ? (
            <div className="rag-response">
              <div className="answer-section">
                <h4>Answer</h4>
                <div className="answer-content">
                  {ragResponse.status === 'loading' ? (
                    <div className="loading-spinner">
                      <div className="spinner"></div>
                      <p>Generating answer...</p>
                    </div>
                  ) : ragResponse.status === 'error' ? (
                    <div className="error-message">
                      Error: {ragResponse.error}
                    </div>
                  ) : (
                    <div dangerouslySetInnerHTML={{ __html: ragResponse.answer.replace(/\n/g, '<br/>') }}></div>
                  )}
                </div>
              </div>
              
              {ragResponse.sources && ragResponse.sources.length > 0 && (
                <div className="sources-section">
                  <h4>Sources</h4>
                  <ul className="sources-list">
                    {ragResponse.sources.map((source, index) => (
                      <li key={index} className="source-item">
                        <span className="source-name">
                          {source.filename || 'Unknown source'}
                        </span>
                        {source.relevance_score && (
                          <span className="source-score">
                            Relevance: {Number(source.relevance_score).toFixed(2)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="no-response">
              <p>Ask a question to generate an answer.</p>
            </div>
          )}
          
          <div className="step-actions">
            <button 
              className="prev-step-button"
              onClick={() => handleStepChange('retrieve')}
            >
              Back: Retrieval
            </button>
            <button 
              className="restart-button"
              onClick={() => {
                setCurrentStep('query');
                setQueryText('');
              }}
            >
              Ask Another Question
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RAGWorkflowInterface;
