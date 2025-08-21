import React, { useState, useEffect } from 'react';
import { Alert, Button, Spinner } from 'react-bootstrap';
import apiClient from '../../api/apiClient';

const ServerStatusMonitor = ({ onStatusChange }) => {
  const [status, setStatus] = useState('checking');
  const [lastChecked, setLastChecked] = useState(null);
  const [message, setMessage] = useState('');
  const [serverInfo, setServerInfo] = useState(null);

  const checkServer = async () => {
    setStatus('checking');
    try {
      const response = await apiClient.get('/health');
      setServerInfo(response.data);
      setStatus('online');
      setMessage('Connected to server successfully');
      if (onStatusChange) {
        onStatusChange('online', response.data);
      }
    } catch (err) {
      console.error('Server connection error:', err);
      setStatus('offline');
      setMessage(`Unable to connect to server: ${err.message}`);
      if (onStatusChange) {
        onStatusChange('offline', null);
      }
    } finally {
      setLastChecked(new Date());
    }
  };

  useEffect(() => {
    checkServer();
    const interval = setInterval(checkServer, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (status === 'checking') {
    return (
      <Alert variant="info">
        <Spinner animation="border" size="sm" className="me-2" />
        Checking server connection...
      </Alert>
    );
  }

  if (status === 'offline') {
    return (
      <Alert variant="danger">
        <Alert.Heading>Server Unavailable</Alert.Heading>
        <p>{message}</p>
        <p>Last checked: {lastChecked?.toLocaleTimeString()}</p>
        <div className="d-flex justify-content-end">
          <Button 
            variant="outline-danger" 
            size="sm" 
            onClick={checkServer}
          >
            Retry Connection
          </Button>
        </div>
      </Alert>
    );
  }

  if (serverInfo) {
    return (
      <Alert variant="success" className="d-flex justify-content-between align-items-center">
        <div>
          <strong>Server Connected</strong>
          {serverInfo.version && <span className="ms-2">Version: {serverInfo.version}</span>}
          {serverInfo.model && <span className="ms-2">Model: {serverInfo.model}</span>}
        </div>
        <small>Last checked: {lastChecked?.toLocaleTimeString()}</small>
      </Alert>
    );
  }

  return null;
};

export default ServerStatusMonitor;
