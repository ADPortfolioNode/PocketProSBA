import React, { useState, useEffect } from 'react';
import { Badge, OverlayTrigger, Tooltip, Button } from 'react-bootstrap';
import PropTypes from 'prop-types';
import connectionService from '../services/connectionService';
import LoadingBar from './LoadingBar';

/**
 * Enhanced ConnectionStatusIndicator with comprehensive backend connectivity
 * Supports multiple environments and provides detailed diagnostics
 */
const ConnectionStatusIndicator = ({
  connected,
  status,
  systemInfo,
  checkInterval = 30000,
  onConnectionChange
}) => {
  const [isChecking, setIsChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState(new Date());
  const [connectionDetails, setConnectionDetails] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Enhanced connection check with multiple strategies
  const checkConnection = async () => {
    if (isChecking) return;
    
    setIsChecking(true);
    
    try {
      const result = await connectionService.checkConnection();
      
      if (result.connected) {
        setConnectionDetails(result);
        if (onConnectionChange) {
          onConnectionChange(true, result.data || result.info);
        }
      } else {
        setConnectionDetails(null);
        if (onConnectionChange) {
          onConnectionChange(false, null, result.error);
        }
      }
      
      setLastChecked(new Date());
    } catch (error) {
      console.error('Connection check failed:', error);
      setConnectionDetails(null);
      if (onConnectionChange) {
        onConnectionChange(false, null, error.message);
      }
    } finally {
      setIsChecking(false);
    }
  };

  // Retry connection with exponential backoff
  const handleRetry = async () => {
    setRetryCount(prev => prev + 1);
    
    // Exponential backoff delay
    const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
    await new Promise(resolve => setTimeout(resolve, delay));
    
    await checkConnection();
  };

  // Initialize connection monitoring
  useEffect(() => {
    // When the parent passes `status` (MainLayout's useConnection), it already
    // polls; don't run a second, competing poll here.
    if (status) return undefined;
    checkConnection(); // Initial check
    
    const intervalId = setInterval(checkConnection, checkInterval);
    
    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checkInterval, retryCount, status]);

  // Format connection info for display
  const getConnectionInfo = () => {
    if (!connectionDetails && !systemInfo) {
      return 'Checking connection...';
    }

    const info = connectionDetails?.data || systemInfo || {};
    const connectionSource = info.server?.self || info.self || info.source;
    
    return (
      <>
        <div><strong>Backend:</strong> {connectionSource || 'Unknown'}</div>
        <div><strong>Status:</strong> {connected ? 'Connected' : (status === 'checking' ? 'Connecting…' : 'Disconnected')}</div>
        {info.server?.self && <div><strong>Server Self:</strong> {info.server.self}</div>}
        {info.source && connectionSource !== info.source && <div><strong>Source:</strong> {info.source}</div>}
        {info.server_type && <div><strong>Type:</strong> {info.server_type}</div>}
        {info.version && <div><strong>Version:</strong> {info.version}</div>}
        {info.uptime && <div><strong>Uptime:</strong> {formatUptime(info.uptime)}</div>}
        {info.models && (
          <div>
            <strong>Models:</strong> {Array.isArray(info.models) 
              ? info.models.join(', ') 
              : 'None available'}
          </div>
        )}
        {info.source && <div><strong>Source:</strong> {info.source}</div>}
        {info.port && <div><strong>Port:</strong> {info.port}</div>}
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

  // Determine badge variant based on connection status. 'checking' is neutral:
  // a check in progress is not a failure.
  const effective = status || (isChecking && !connectionDetails ? 'checking' : (connected ? 'online' : 'offline'));
  const badgeVariant = effective === 'online' ? 'success' : effective === 'offline' ? 'danger' : 'light';
  const statusText = effective === 'online' ? 'Connected' : effective === 'offline' ? 'Offline' : 'Connecting…';

  return (
    <OverlayTrigger
      placement="bottom"
      overlay={
        <Tooltip id="connection-status-tooltip">
          <div className="connection-tooltip" style={{ maxWidth: '300px' }}>
            {getConnectionInfo()}
            <div className="text-center mt-2">
              <small>Click to check connection</small>
              {!connected && (
                <div className="mt-2">
                  <Button 
                    variant="outline-danger" 
                    size="sm" 
                    onClick={handleRetry} 
                    disabled={isChecking}
                  >
                    {isChecking ? 'Checking...' : 'Retry'}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </Tooltip>
      }
    >
      <Badge 
        bg={badgeVariant} 
        text={badgeVariant === 'light' ? 'dark' : undefined}
        className="connection-status-badge"
        style={{ cursor: 'pointer' }}
        onClick={() => checkConnection()}
        data-testid="connection-badge"
        data-status={effective}
      >
        {effective === 'checking' ? (
          <LoadingBar inline label={statusText} />
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

ConnectionStatusIndicator.propTypes = {
  connected: PropTypes.bool.isRequired,
  status: PropTypes.oneOf(['checking', 'online', 'offline']),
  systemInfo: PropTypes.object,
  checkInterval: PropTypes.number,
  onConnectionChange: PropTypes.func
};

export default ConnectionStatusIndicator;
