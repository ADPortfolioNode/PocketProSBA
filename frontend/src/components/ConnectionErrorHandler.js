import React from 'react';

/**
 * ConnectionErrorHandler Component
 * 
 * Displays a user-friendly error message when connection to the backend fails,
 * providing retry and reload options.
 * 
 * Props:
 * - error: The error object or message
 * - onRetry: Function to retry the connection
 * - fallbackActive: Boolean indicating if a fallback connection method is active
 */
const ConnectionErrorHandler = ({ error, onRetry, fallbackActive }) => {
  // Extract a more user-friendly message from the error
  const getErrorMessage = () => {
    if (!error) return "Unable to connect to the server";
    
    if (error.toString().includes("Unexpected token '<'")) {
      return "The server returned HTML instead of the expected JSON data. This usually indicates the API server is not responding correctly.";
    }
    
    if (error.toString().includes("Failed to fetch") || error.toString().includes("NetworkError")) {
      return "Network connection failed. The server might be down or unreachable.";
    }
    
    return error.toString();
  };

  return (
    <div className="connection-error-container">
      <div className="connection-error-icon">❌</div>
      <h2 className="connection-error-title">Connection Error</h2>
      <div className="connection-error-message">
        <p>{getErrorMessage()}</p>
        <p>Please check your internet connection and try again.</p>
      </div>
      
      {fallbackActive && (
        <div className="connection-fallback-message">
          Using fallback connection method. Some features may be limited.
        </div>
      )}
      
      <div className="connection-error-actions">
        <button 
          className="connection-retry-button" 
          onClick={onRetry}
        >
          Retry Connection
        </button>
        <button 
          className="connection-retry-button" 
          onClick={() => window.location.reload()}
        >
          Reload Page
        </button>
      </div>
    </div>
  );
};

export default ConnectionErrorHandler;
