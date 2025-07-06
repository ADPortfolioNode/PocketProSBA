import React, { Component } from 'react';
import { Alert, Button, Card } from 'react-bootstrap';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      timestamp: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Catch errors in any components below and re-render with error message
    this.setState({
      error: error,
      errorInfo: errorInfo,
      timestamp: new Date().toISOString()
    });
    
    // Log error to an error reporting service
    console.error("Uncaught error:", error, errorInfo);
    
    // Could also send to a logging service here
    // logErrorToService(error, errorInfo);
  }

  resetErrorBoundary = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      timestamp: null
    });
    
    // Call the onReset callback if provided
    if (this.props.onReset) {
      this.props.onReset();
    }
  }

  render() {
    if (this.state.hasError) {
      // Render fallback UI
      return (
        <Card className="error-boundary-card">
          <Card.Header className="bg-danger text-white">
            <h5>Something went wrong</h5>
          </Card.Header>
          <Card.Body>
            <Alert variant="danger">
              <p><strong>Error:</strong> {this.state.error && this.state.error.toString()}</p>
              {this.props.showDetails && (
                <details style={{ whiteSpace: 'pre-wrap' }}>
                  <summary>Error Details</summary>
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </details>
              )}
              <p className="text-muted mt-2">Timestamp: {this.state.timestamp}</p>
            </Alert>
            <div className="d-flex justify-content-between">
              <Button 
                variant="primary" 
                onClick={this.resetErrorBoundary}
              >
                Try Again
              </Button>
              {this.props.fallbackComponent && (
                <Button 
                  variant="secondary" 
                  onClick={() => this.props.onFallback && this.props.onFallback()}
                >
                  Switch to Fallback Mode
                </Button>
              )}
            </div>
            {this.props.fallbackComponent && this.props.showFallback && (
              <div className="mt-3">
                {this.props.fallbackComponent}
              </div>
            )}
          </Card.Body>
        </Card>
      );
    }

    // If there's no error, render children normally
    return this.props.children;
  }
}

export default ErrorBoundary;
