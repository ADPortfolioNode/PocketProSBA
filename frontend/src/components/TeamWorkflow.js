import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './TeamWorkflow.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const TeamWorkflow = () => {
  const [issueDescription, setIssueDescription] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [greeting, setGreeting] = useState('');
  const [processing, setProcessing] = useState(false);
  const chatEndRef = useRef(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversationHistory]);

  // Poll for updates when task is processing
  useEffect(() => {
    let interval;
    if (processing && taskId) {
      interval = setInterval(async () => {
        await fetchTaskStatus(taskId);
        await fetchConversationHistory(taskId);
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [processing, taskId]);

  const submitIssue = async () => {
    if (!issueDescription.trim()) {
      alert('Please enter an issue description');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/team/submit`, {
        issue_description: issueDescription
      });

      setTaskId(response.data.task_id);
      setGreeting(response.data.greeting);
      setTaskStatus({
        status: response.data.status,
        iterations: 0,
        validation_passed: false
      });

      // Fetch initial conversation history
      await fetchConversationHistory(response.data.task_id);

      // Automatically start processing
      await processTask(response.data.task_id);
    } catch (error) {
      console.error('Error submitting issue:', error);
      alert('Failed to submit issue. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const processTask = async (id) => {
    const taskIdToProcess = id || taskId;
    if (!taskIdToProcess) return;

    setProcessing(true);
    try {
      const response = await axios.post(`${API_URL}/api/team/process/${taskIdToProcess}`);
      setTaskStatus(response.data);

      // Fetch final conversation history
      await fetchConversationHistory(taskIdToProcess);
    } catch (error) {
      console.error('Error processing task:', error);
      alert('Failed to process task. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const fetchTaskStatus = async (id) => {
    try {
      const response = await axios.get(`${API_URL}/api/team/task/${id}`);
      setTaskStatus(response.data);
    } catch (error) {
      console.error('Error fetching task status:', error);
    }
  };

  const fetchConversationHistory = async (id) => {
    try {
      const response = await axios.get(`${API_URL}/api/team/task/${id}/history`);
      setConversationHistory(response.data.conversation);
      if (response.data.greeting) {
        setGreeting(response.data.greeting);
      }
    } catch (error) {
      console.error('Error fetching conversation history:', error);
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'administrator':
        return '🔍';
      case 'developer':
        return '💻';
      case 'qa':
        return '✅';
      default:
        return '👤';
    }
  };

  const getRoleName = (role) => {
    switch (role) {
      case 'administrator':
        return 'Administrator';
      case 'developer':
        return 'Developer';
      case 'qa':
        return 'QA Engineer';
      default:
        return role;
    }
  };

  const getRoleClass = (role) => {
    return `message-${role}`;
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { text: 'Pending', class: 'badge-pending' },
      researching: { text: 'Researching', class: 'badge-researching' },
      implementing: { text: 'Implementing', class: 'badge-implementing' },
      validating: { text: 'Validating', class: 'badge-validating' },
      completed: { text: 'Completed', class: 'badge-completed' },
      failed: { text: 'Failed', class: 'badge-failed' }
    };
    return badges[status] || { text: status, class: 'badge-default' };
  };

  return (
    <div className="team-workflow-container">
      <div className="team-workflow-header">
        <h1>🎯 World-Class Development Team</h1>
        <p className="greeting">{greeting || 'Hello deo!'}</p>
        <p className="subtitle">Submit your issue and watch our expert team collaborate to resolve it</p>
      </div>

      {!taskId ? (
        <div className="issue-submission">
          <h2>Submit Your Issue</h2>
          <textarea
            className="issue-input"
            value={issueDescription}
            onChange={(e) => setIssueDescription(e.target.value)}
            placeholder="Describe the issue you need help with..."
            rows={6}
            disabled={loading}
          />
          <button
            className="submit-button"
            onClick={submitIssue}
            disabled={loading || !issueDescription.trim()}
          >
            {loading ? 'Submitting...' : 'Submit Issue to Team'}
          </button>
        </div>
      ) : (
        <div className="task-view">
          {/* Status Bar */}
          {taskStatus && (
            <div className="status-bar">
              <div className="status-info">
                <span className="status-label">Status:</span>
                <span className={`badge ${getStatusBadge(taskStatus.status).class}`}>
                  {getStatusBadge(taskStatus.status).text}
                </span>
              </div>
              <div className="status-info">
                <span className="status-label">Iterations:</span>
                <span className="badge badge-default">{taskStatus.iterations}</span>
              </div>
              {taskStatus.validation_passed && (
                <div className="status-info">
                  <span className="badge badge-success">✓ Validation Passed</span>
                </div>
              )}
            </div>
          )}

          {/* Team Panels */}
          <div className="team-panels">
            <div className="team-panel administrator-panel">
              <div className="panel-header">
                <span className="panel-icon">🔍</span>
                <h3>Administrator</h3>
                <p>Researches & Analyzes</p>
              </div>
              <div className="panel-content">
                {conversationHistory
                  .filter(msg => msg.role === 'administrator')
                  .slice(-2)
                  .map(msg => (
                    <div key={msg.id} className="panel-message">
                      <div className="message-time">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="message-content">
                        {msg.content}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            <div className="team-panel developer-panel">
              <div className="panel-header">
                <span className="panel-icon">💻</span>
                <h3>Developer</h3>
                <p>Implements Solutions</p>
              </div>
              <div className="panel-content">
                {conversationHistory
                  .filter(msg => msg.role === 'developer')
                  .slice(-2)
                  .map(msg => (
                    <div key={msg.id} className="panel-message">
                      <div className="message-time">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="message-content">
                        {msg.content}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            <div className="team-panel qa-panel">
              <div className="panel-header">
                <span className="panel-icon">✅</span>
                <h3>QA Engineer</h3>
                <p>Validates & Tests</p>
              </div>
              <div className="panel-content">
                {conversationHistory
                  .filter(msg => msg.role === 'qa')
                  .slice(-2)
                  .map(msg => (
                    <div key={msg.id} className="panel-message">
                      <div className="message-time">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="message-content">
                        {msg.content}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>

          {/* Full Conversation History */}
          <div className="conversation-history">
            <h3>Full Team Conversation</h3>
            <div className="messages-container">
              {conversationHistory.map((msg) => (
                <div key={msg.id} className={`message ${getRoleClass(msg.role)}`}>
                  <div className="message-header">
                    <span className="message-icon">{getRoleIcon(msg.role)}</span>
                    <span className="message-role">{getRoleName(msg.role)}</span>
                    <span className="message-timestamp">
                      {new Date(msg.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="message-body">
                    <pre>{msg.content}</pre>
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="action-buttons">
            {processing && (
              <div className="processing-indicator">
                <div className="spinner"></div>
                <span>Team is working on your issue...</span>
              </div>
            )}
            <button
              className="new-issue-button"
              onClick={() => {
                setTaskId(null);
                setTaskStatus(null);
                setConversationHistory([]);
                setIssueDescription('');
              }}
              disabled={processing}
            >
              Submit New Issue
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamWorkflow;
