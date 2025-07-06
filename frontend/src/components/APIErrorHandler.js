import React, { useState } from 'react';
import { Alert, Button, Collapse, Spinner } from 'react-bootstrap';

/**
 * Component for handling and displaying API errors with retry functionality
 * 
 * @param {Object} props - Component properties
 * @param {Object} props.error - Error object with message and code
 * @param {Function} props.onRetry - Function to call when retry button is clicked
 * @param {string} props.variant - Bootstrap variant for the alert (default: 'danger')
 * @param {boolean} props.dismissible - Whether the alert can be dismissed
 * @param {Component} props.fallbackUI - UI to show as fallback when error occurs
 * @param {boolean} props.showDetails - Whether to show technical details
 * @param {boolean} props.isRetrying - Whether a retry is in progress
 * @param {string} props.resourceType - Type of resource that failed (e.g., "document", "chat")
 */
const APIErrorHandler = ({ 
  error, 
  onRetry, 
  variant = 'danger', 
  dismissible = true,
  fallbackUI = null,
  showDetails = false,
  isRetrying = false,
  resourceType = 'resource'
}) => {
  const [dismissed, setDismissed] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  
  if (!error || dismissed) return null;
  
  // Get user-friendly message based on error
  const getFriendlyMessage = () => {
    if (typeof error === 'string') return error;
    
    // Handle common HTTP error codes
    if (error.status === 404) {
      return `The requested ${resourceType} could not be found. It may have been moved or deleted.`;
    } else if (error.status === 401) {
      return `You need to be logged in to access this ${resourceType}.`;
    } else if (error.status === 403) {
      return `You don't have permission to access this ${resourceType}.`;
    } else if (error.status >= 500) {
      return `The server encountered a problem while processing your request. Our team has been notified.`;
    } else if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
      return `The request timed out. Please check your internet connection and try again.`;
    } else if (error.code === 'ERR_NETWORK') {
      return `Network error. Please check your internet connection and try again.`;
    }
    
    return error.message || `An error occurred while loading the ${resourceType}.`;
  };
  
  const getTechnicalDetails = () => {
    if (typeof error === 'string') return error;
    
    return JSON.stringify({
      message: error.message,
      code: error.code,
      status: error.status,
      statusText: error.statusText,
      timestamp: new Date().toISOString(),
      url: error.config?.url,
      method: error.config?.method
    }, null, 2);
  };
  
  const handleDismiss = () => {
    setDismissed(true);
  };
  
  return (
    <Alert 
      variant={variant} 
      onClose={dismissible ? handleDismiss : undefined}
      dismissible={dismissible}
    >
      <Alert.Heading>
        {error.status ? `Error ${error.status}` : 'Error'}
      </Alert.Heading>
      
      <p>{getFriendlyMessage()}</p>
      
      {showDetails && (
        <>
          <Button 
            variant="link" 
            size="sm" 
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="p-0 mb-2"
          >
            {showTechnicalDetails ? 'Hide' : 'Show'} Technical Details
          </Button>
          
          <Collapse in={showTechnicalDetails}>
            <pre className="mt-2 p-2 bg-light border rounded">
              <code>{getTechnicalDetails()}</code>
            </pre>
          </Collapse>
        </>
      )}
      
      <div className="d-flex justify-content-between mt-3">
        {onRetry && (
          <Button 
            variant="outline-light" 
            onClick={onRetry}
            disabled={isRetrying}
          >
            {isRetrying ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Retrying...
              </>
            ) : (
              'Retry'
            )}
          </Button>
        )}
      </div>
      
      {fallbackUI && (
        <div className="mt-3">
          <hr />
          <p className="text-white">You can try an alternative option:</p>
          {fallbackUI}
        </div>
      )}
    </Alert>
  );
};

export default APIErrorHandler;
