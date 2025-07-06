import React from 'react';
import { Spinner, Alert, Container, Row, Col } from 'react-bootstrap';

/**
 * Component for displaying various loading states with customizable appearance
 * 
 * @param {Object} props - Component properties
 * @param {string} props.type - Type of loader ('spinner', 'progress', 'skeleton')
 * @param {string} props.size - Size of loader ('sm', 'md', 'lg')
 * @param {string} props.text - Text to display with the loader
 * @param {string} props.variant - Bootstrap variant for styling
 * @param {boolean} props.fullPage - Whether the loader should take up the full page
 * @param {number} props.progress - Progress value (0-100) for progress type
 * @param {number} props.delay - Delay in ms before showing the loader
 */
const LoadingIndicator = ({
  type = 'spinner',
  size = 'md',
  text = 'Loading...',
  variant = 'primary',
  fullPage = false,
  progress = null,
  delay = 0
}) => {
  const [visible, setVisible] = React.useState(delay === 0);

  React.useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => setVisible(true), delay);
      return () => clearTimeout(timer);
    }
  }, [delay]);
  
  if (!visible) return null;
  
  // Different loader types
  const renderLoader = () => {
    switch (type) {
      case 'spinner':
        return (
          <div className="text-center">
            <Spinner
              animation="border"
              role="status"
              variant={variant}
              className={`mb-2 loader-${size}`}
            >
              <span className="visually-hidden">{text}</span>
            </Spinner>
            {text && <div className="mt-2">{text}</div>}
          </div>
        );
        
      case 'dots':
        return (
          <div className="dots-loader-container text-center">
            <div className={`dots-loader dots-loader-${size}`}>
              <div className={`dot dot-1 bg-${variant}`}></div>
              <div className={`dot dot-2 bg-${variant}`}></div>
              <div className={`dot dot-3 bg-${variant}`}></div>
            </div>
            {text && <div className="mt-2">{text}</div>}
          </div>
        );
        
      case 'progress':
        return (
          <div>
            <div className="progress" style={{ height: size === 'sm' ? '0.5rem' : size === 'lg' ? '1.5rem' : '1rem' }}>
              <div
                className={`progress-bar progress-bar-striped progress-bar-animated bg-${variant}`}
                role="progressbar"
                style={{ width: `${progress || 100}%` }}
                aria-valuenow={progress || 100}
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {size === 'lg' && `${progress || ''}${progress ? '%' : ''}`}
              </div>
            </div>
            {text && <div className="text-center mt-2">{text}</div>}
          </div>
        );
        
      case 'skeleton':
        return (
          <div>
            <div className="skeleton-loader">
              <div className={`skeleton-line skeleton-${size} w-75 mb-2`}></div>
              <div className={`skeleton-line skeleton-${size} w-100 mb-2`}></div>
              <div className={`skeleton-line skeleton-${size} w-50`}></div>
            </div>
            {text && <div className="text-center mt-2 text-muted">{text}</div>}
          </div>
        );
        
      default:
        return (
          <Alert variant="info">
            {text || 'Loading...'}
          </Alert>
        );
    }
  };
  
  // Render based on fullPage setting
  if (fullPage) {
    return (
      <Container fluid className="fullpage-loader d-flex align-items-center justify-content-center">
        <Row className="w-100 justify-content-center">
          <Col xs={12} md={6} lg={4} className="text-center">
            {renderLoader()}
          </Col>
        </Row>
      </Container>
    );
  }
  
  return renderLoader();
};

export default LoadingIndicator;
