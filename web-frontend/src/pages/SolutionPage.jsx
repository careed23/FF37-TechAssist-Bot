import { useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header.jsx';
import { logSession } from '../api.js';

export default function SolutionPage() {
  const { flowId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [selected, setSelected] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const { solution, flowName, startTime, stepsTaken } = location.state ?? {};

  if (!solution) {
    return (
      <div className="container">
        <Header />
        <div className="error">
          Session data not found. Please start a new troubleshooting session.
        </div>
        <div className="footer-actions" style={{ marginTop: '16px' }}>
          <button onClick={() => navigate('/')}>Back to Home</button>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selected) {
      setError('Please confirm the outcome to complete this session.');
      return;
    }
    setSubmitting(true);
    setError(null);

    const resolved = selected === 'yes';
    const endTime = new Date().toISOString();
    const duration = startTime
      ? (new Date(endTime) - new Date(startTime)) / 1000
      : 0;

    try {
      await logSession({
        flow_id: flowId,
        flow_name: flowName,
        solution_id: solution.id,
        steps_taken: stepsTaken ?? [],
        resolved,
        start_time: startTime,
        end_time: endTime,
        duration,
      });
      navigate('/complete', { state: { resolved, flowName } });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container">
      <Header />
      <h2>Resolution: {solution.title}</h2>
      <p className="subheading">{flowName}</p>
      <ol>
        {solution.steps.map((step, i) => (
          <li key={i}>{step}</li>
        ))}
      </ol>

      {(solution.reference_doc || solution.video) && (
        <div className="metadata">
          {solution.reference_doc && (
            <div>
              <strong>Reference:</strong>{' '}
              <a
                href={solution.reference_doc}
                target="_blank"
                rel="noopener noreferrer"
              >
                {solution.reference_doc}
              </a>
            </div>
          )}
          {solution.video && (
            <div>
              <strong>Video:</strong>{' '}
              <a
                href={solution.video}
                target="_blank"
                rel="noopener noreferrer"
              >
                {solution.video}
              </a>
            </div>
          )}
        </div>
      )}

      {solution.escalate_if && (
        <div className="callout">
          <strong>Escalate if:</strong> {solution.escalate_if}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div>
          <label>
            <input
              type="radio"
              name="resolved"
              value="yes"
              checked={selected === 'yes'}
              onChange={() => setSelected('yes')}
            />{' '}
            Issue resolved
          </label>
        </div>
        <div>
          <label>
            <input
              type="radio"
              name="resolved"
              value="no"
              checked={selected === 'no'}
              onChange={() => setSelected('no')}
            />{' '}
            Needs escalation
          </label>
        </div>
        <div className="footer-actions">
          <button type="submit" disabled={submitting}>
            {submitting ? 'Saving…' : 'Complete Session'}
          </button>
          <button
            type="button"
            className="glass"
            onClick={() => navigate('/')}
          >
            Start Over
          </button>
        </div>
      </form>
    </div>
  );
}
