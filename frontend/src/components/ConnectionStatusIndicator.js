import React, { useState, useEffect } from 'react';
import { Badge, OverlayTrigger, Tooltip, Spinner } from 'react-bootstrap';

/**
 * Component for displaying the current connection status to the backend
 * 
 * @param {Object} props - Component properties
 * @param {boolean} props.connected - Whether the application is connected to the backend
 * @param {Object} props.systemInfo - System information from the backend
 * @param {string} props.apiUrl - The API URL being used
 * @param {number} props.checkInterval - Interval in ms to check connection (default: 30000)
 * @param {Function} props.onConnectionChange - Callback when connection status changes
 */
const ConnectionStatusIndicator = ({
  connected,
  systemInfo,
  apiUrl,
  checkInterval = 30000,
  onConnectionChange
}) => {
  const [isChecking, setIsChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState(new Date());
  
  // Define multiple health endpoints for fallback
  const healthEndpoints = [
    '/api/health',
    '/health'
  ];

  // Function to validate content type and parse response safely
  const safeParseResponse = async (response) => {
    try {
      // Check content-type to make sure it's not HTML
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('text/html')) {
        console.warn('Received HTML response instead of expected JSON');
        throw new Error('Received HTML instead of JSON');
      }
      
      const text = await response.text();
      try {
        // Try to parse as JSON
        return { isJson: true, data: JSON.parse(text) };
      } catch (e) {
        // If parsing fails, return the text
        console.warn('Failed to parse response as JSON:', e);
        return { isJson: false, data: text };
      }
    } catch (e) {
      return { isJson: false, error: e };
    }
  };

  // Function to check connection with fallback options
  const checkConnection = async () => {
    if (isChecking) return;
    
    setIsChecking(true);
    let errorDetails = null;
    
    // Try all endpoints in order until one works
    for (const path of healthEndpoints) {
      try {
        const endpoint = path;  // Use the relative path directly
        
        // First try with a HEAD request to minimize data transfer
        try {
          const headResponse = await fetch(endpoint, { method: 'HEAD' });
          if (headResponse.ok) {
            if (onConnectionChange && connected !== true) {
              onConnectionChange(true, { server_type: 'Unknown (HEAD check)' });
            }
            setLastChecked(new Date());
            setIsChecking(false);
            return;
          }
        } catch (headError) {
          // If HEAD fails, continue to full GET request
          console.debug('HEAD request failed, trying GET:', headError);
        }
        
        // Try a full GET request
        const response = await fetch(endpoint);
        if (!response.ok) continue; // Try next endpoint if this one fails
        
        const { isJson, data, error } = await safeParseResponse(response);
        
        if (isJson && data) {
          if (onConnectionChange && connected !== true) {
            onConnectionChange(true, data);
          }
          setLastChecked(new Date());
          setIsChecking(false);
          return;
        } else if (response.ok) {
          // Response is OK but not JSON, still consider connected
          if (onConnectionChange && connected !== true) {
            onConnectionChange(true, { server_type: 'Unknown (non-JSON response)' });
          }
          setLastChecked(new Date());
          setIsChecking(false);
          return;
        }
      } catch (error) {
        errorDetails = error;
        console.warn(`Connection check failed for ${path}:`, error);
        // Continue to next endpoint
      }
    }
    
    // If we get here, all endpoints failed
    console.error('All connection endpoints failed:', errorDetails);
    if (onConnectionChange && connected !== false) {
      onConnectionChange(false, null, errorDetails);
    }
    
    setLastChecked(new Date());
    setIsChecking(false);
  };
  
  // Set up interval to check connection periodically
  useEffect(() => {
    const intervalId = setInterval(checkConnection, checkInterval);
    return () => clearInterval(intervalId);
  }, [checkInterval, connected]);
  
  // Format backend info for display
  const getBackendInfo = () => {
    if (!systemInfo) return 'No system info available';
    
    return (
      <>
        <div><strong>Server:</strong> {systemInfo.server_type || 'Unknown'}</div>
        <div><strong>Version:</strong> {systemInfo.version || 'Unknown'}</div>
        {systemInfo.uptime && <div><strong>Uptime:</strong> {formatUptime(systemInfo.uptime)}</div>}
        {systemInfo.models && (
          <div>
            <strong>Models:</strong> {Array.isArray(systemInfo.models) 
              ? systemInfo.models.join(', ') 
              : 'None available'}
          </div>
        )}
        <div className="text-muted mt-2">Last checked: {formatTime(lastChecked)}</div>
      </>
    );
  };
  
  // Format uptime in a readable way
  const formatUptime = (seconds) => {
    if (!seconds && seconds !== 0) return 'Unknown';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`);
    
    return parts.join(' ');
  };
  
  // Format time for last checked
  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  
  // Determine badge variant based on connection status
  const badgeVariant = connected ? 'success' : 'danger';
  const statusText = connected ? 'Connected' : 'Disconnected';
  
  return (
    <OverlayTrigger
      placement="bottom"
      overlay={
        <Tooltip id="connection-status-tooltip">
          <div className="connection-tooltip">
            {getBackendInfo()}
            <div className="text-center mt-2">
              <small>Click to check connection</small>
            </div>
          </div>
        </Tooltip>
      }
    >
      <Badge 
        bg={badgeVariant} 
        className="connection-status-badge"
        style={{ cursor: 'pointer' }}
        onClick={() => checkConnection()}
      >
        {isChecking ? (
          <>
            <Spinner animation="border" size="sm" className="me-1" />
            Checking...
          </>
        ) : (
          <>
            <span className={`connection-indicator ${connected ? 'connected' : 'disconnected'}`}>⬤</span>
            {statusText}
          </>
        )}
      </Badge>
    </OverlayTrigger>
  );
};

export default ConnectionStatusIndicator;
