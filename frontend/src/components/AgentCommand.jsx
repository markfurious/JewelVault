import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AgentCommand.css';

const API_BASE = 'http://localhost:8000/api/v1';

const AGENT_SUGGESTIONS = [
  "Restock low inventory products",
  "Update prices based on gold increase",
  "Create 1ct round diamond VS1 G color 18K white gold ring",
  "Detect anomalies in last 24 hours",
  "Generate cross-sell recommendations for rings",
  "Flag dead stock for discount",
];

function AgentCommand() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dryRun, setDryRun] = useState(true);
  const [health, setHealth] = useState(null);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/ai/health`);
      const data = await res.json();
      setHealth(data);
    } catch (e) {
      setHealth({ status: 'error', message: e.message });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/ai/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, dry_run: dryRun }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Agent execution failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
  };

  return (
    <div className="agent-command">
      <div className="agent-header">
        <h2>AI Agent Command Center</h2>
        <div className="header-actions">
          <button onClick={() => navigate('/agent-requests')} className="requests-btn">
            Agent Requests
          </button>
          <button onClick={checkHealth} className="health-btn">
            Check Health
          </button>
        </div>
      </div>

      {health && (
        <div className={`health-status ${health.status}`}>
          <span className="status-indicator">
            {health.status === 'healthy' ? '●' : '○'}
          </span>
          System: {health.status.toUpperCase()}
          {health.status === 'healthy' && (
            <span className="health-details">
              {' '}| DB: {health.database_connected ? '✓' : '✗'}
              {' '}| Claude API: {health.claude_api_connected ? '✓' : '✗'}
            </span>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="agent-form">
        <div className="input-row">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a command for the AI agents..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Executing...' : 'Run Agent'}
          </button>
        </div>

        <label className="dry-run-toggle">
          <input
            type="checkbox"
            checked={dryRun}
            onChange={(e) => setDryRun(e.target.checked)}
          />
          Dry Run Mode (simulate without DB changes)
        </label>
      </form>

      <div className="suggestions">
        <span>Try:</span>
        {AGENT_SUGGESTIONS.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => handleSuggestionClick(suggestion)}
            className="suggestion-chip"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="result">
          <div className="result-header">
            <h3>Execution Result</h3>
            <span className={`status-badge ${result.status}`}>
              {result.status}
            </span>
          </div>

          <div className="result-info">
            <p><strong>Agent:</strong> {result.agent}</p>
            {result.intent && <p><strong>Intent:</strong> {result.intent}</p>}
            <p><strong>Dry Run:</strong> {result.dry_run ? 'Yes' : 'No'}</p>
          </div>

          <div className="action-taken">
            <strong>Action Taken:</strong>
            <p>{result.action_taken}</p>
          </div>

          {result.actions && result.actions.length > 0 && (
            <div className="actions-list">
              <strong>Actions ({result.actions.length})</strong>
              <div className="actions-scroll">
                {result.actions.slice(0, 50).map((action, i) => (
                  <div key={i} className="action-item">
                    <div className="action-header">
                      <span className="action-type">{action.action_type}</span>
                      <span className="action-entity">{action.entity_type}</span>
                    </div>
                    <p className="action-desc">{action.description}</p>
                    {action.entity_id && (
                      <p className="action-id">ID: {action.entity_id.slice(0, 8)}...</p>
                    )}
                    {action.data && Object.keys(action.data).length > 0 && (
                      <pre className="action-data">
                        {JSON.stringify(action.data, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
                {result.actions.length > 50 && (
                  <p className="more-actions">
                    ... and {result.actions.length - 50} more actions
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AgentCommand;
