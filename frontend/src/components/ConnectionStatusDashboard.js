import React, { useState, useEffect } from 'react';
import { Card, Alert, Button, Badge } from 'react-bootstrap';
import { useConnection } from '../hooks/useConnection';

const ConnectionStatusDashboard = () => {
  const {
    serverConnected,
    backendError,
    isCheckingHealth,
    connectionInfo,
    consecutiveFailures,
    circuitBreakerOpen,
    checkConnection,
    getDiagnostics,
    resetConnection,
  } = useConnection();

  const [diagnostics, setDiagnostics] = useState(null);
  const [connectionStats, setConnectionStats] = useState(null);

  useEffect(() => {
    const fetchDiagnostics = async () => {
      try {
        const diag = await getDiagnostics();
        setDiagnostics(diag);
      } catch (error) {
        console.error('Failed to fetch diagnostics:', error);
      }
    };

    const fetchConnectionStats = async () => {
      try {
        const response = await fetch('/api/connection-stats');
        const stats = await response.json();
        setConnectionStats(stats);
      } catch (error) {
        console.error('Failed to fetch connection stats:', error);
      }
    };

    if (serverConnected) {
      fetchDiagnostics();
      fetchConnectionStats();
    }
  }, [serverConnected, getDiagnostics]);

  const getConnectionStatus = () => {
    if (circuitBreakerOpen) return { status: 'danger', text: 'Circuit Breaker Open' };
    if (!serverConnected) return { status: 'danger', text: 'Disconnected' };
    if (consecutiveFailures > 0) return { status: 'warning', text: 'Unstable' };
    return { status: 'success', text: 'Connected' };
  };

  const connectionStatus = getConnectionStatus();

  const StatusCard = ({ title, value, subtitle, status = 'info' }) => (
    <Card className={`status-card ${status} mb-3`}>
      <Card.Body>
        <Card.Title>{title}</Card.Title>
        <Card.Subtitle className="mb-2 text-muted">{subtitle}</Card.Subtitle>
        <h3>{value}</h3>
      </Card.Body>
    </Card>
  );

  return (
    <div className="connection-dashboard">
      <StatusCard
        title="Connection Status"
        value={connectionStatus.text}
        subtitle={serverConnected ? 'Backend reachable' : 'Backend unreachable'}
        status={connectionStatus.status}
      />

      <StatusCard
        title="Active Connections"
        value={diagnostics?.connection_health?.active_connections ?? 'N/A'}
        subtitle="Current active connections"
        status="info"
      />

      <StatusCard
        title="Avg Response Time"
        value={diagnostics?.connection_health?.average_response_time
          ? `${(diagnostics.connection_health.average_response_time * 1000).toFixed(0)} ms`
          : 'N/A'}
        subtitle="Average response time"
        status={diagnostics?.connection_health?.average_response_time < 0.5 ? 'success' : 'warning'}
      />

      <StatusCard
        title="Error Rate"
        value={diagnostics?.connection_health?.error_rate
          ? `${(diagnostics.connection_health.error_rate * 100).toFixed(1)}%`
          : 'N/A'}
        subtitle="Request error percentage"
        status={diagnostics?.connection_health?.error_rate < 0.05 ? 'success' : 'danger'}
      />

      {circuitBreakerOpen && (
        <Alert variant="warning" className="mt-3">
          <Alert.Heading>Circuit Breaker Active</Alert.Heading>
          <p>Too many connection failures detected. Automatic retry in progress.</p>
          <div className="d-flex gap-2">
            <Button variant="outline-warning" onClick={resetConnection}>
              Reset Circuit Breaker
            </Button>
            <Button variant="outline-info" onClick={checkConnection}>
              Test Connection
            </Button>
          </div>
        </Alert>
      )}

      {diagnostics && (
        <Card className="mt-3">
          <Card.Body>
            <Card.Title>Connection Details</Card.Title>
            <ul>
              <li>Service: {diagnostics.service || 'PocketPro SBA'}</li>
              <li>Version: {diagnostics.version || '1.0.0'}</li>
              <li>
                Uptime:{' '}
                {diagnostics.connection_health?.uptime
                  ? `${Math.floor(diagnostics.connection_health.uptime / 3600)}h ${Math.floor(
                      (diagnostics.connection_health.uptime % 3600) / 60
                    )}m`
                  : 'N/A'}
              </li>
              <li>Total Requests: {diagnostics.connection_health?.total_requests ?? 'N/A'}</li>
            </ul>
          </Card.Body>
        </Card>
      )}

      {connectionStats && (
        <Card className="mt-3">
          <Card.Body>
            <Card.Title>Request Statistics</Card.Title>
            <ul>
              {Object.entries(connectionStats.endpoint_stats || {}).map(([endpoint, count]) => (
                <li key={endpoint}>
                  {endpoint}: <Badge bg="primary">{count}</Badge>
                </li>
              ))}
              <li>
                Success Rate:{' '}
                {connectionStats.success_rate ? `${connectionStats.success_rate.toFixed(1)}%` : 'N/A'}
              </li>
            </ul>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default ConnectionStatusDashboard;
