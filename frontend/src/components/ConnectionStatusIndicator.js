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
  
  // Function to check connection
  const checkConnection = async () => {
    if (isChecking) return;
    
    setIsChecking(true);
    try {
      // Use relative URL instead of including apiUrl to avoid CORS issues
      const endpoint = apiUrl ? `${apiUrl}/api/health` : '/api/health';
      const response = await fetch(endpoint);
      const newStatus = response.ok;
      const data = response.ok ? await response.json() : null;
      
      if (onConnectionChange && connected !== newStatus) {
        onConnectionChange(newStatus, data);
      }
      
      setLastChecked(new Date());
    } catch (error) {
      console.error('Connection check failed:', error);
      if (onConnectionChange && connected !== false) {
        onConnectionChange(false, null);
      }
    } finally {
      setIsChecking(false);
    }
  };
  
  // Set up interval to check connection periodically
  useEffect(() => {
    const intervalId = setInterval(checkConnection, checkInterval);
    return () => clearInterval(intervalId);
  }, [checkInterval, connected, apiUrl]);
  
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
