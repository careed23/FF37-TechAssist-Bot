import { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header.jsx';
import { getStep, submitStep } from '../api.js';

export default function FlowStepPage() {
  const { flowId, stepId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [step, setStep] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Session state passed via router; initialise defaults if navigated directly
  const sessionState = location.state ?? {
    flowName: '',
    startTime: new Date().toISOString(),
    stepsTaken: [],
  };

  useEffect(() => {
    setLoading(true);
    setSelected('');
    setError(null);
    getStep(flowId, stepId)
      .then((data) => {
        setStep(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [flowId, stepId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selected) {
      setError('Please select an option to continue.');
      return;
    }
    setSubmitting(true);
    setError(null);

    try {
      const selectedOption = step.options.find((o) => o.value === selected);
      const result = await submitStep(flowId, stepId, selected);

      const newStepsTaken = [
        ...sessionState.stepsTaken,
        {
          step_id: step.id,
          question: step.question,
          answer: selected,
          answer_description: selectedOption?.description ?? '',
        },
      ];

      if (result.type === 'step') {
        navigate(`/flow/${flowId}/step/${result.data.id}`, {
          state: { ...sessionState, stepsTaken: newStepsTaken },
        });
      } else if (result.type === 'solution') {
        navigate(`/flow/${flowId}/solution/${result.data.id}`, {
          state: {
            ...sessionState,
            stepsTaken: newStepsTaken,
            solution: result.data,
          },
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="container">
      <Header />
      <p className="loading">Loading step…</p>
    </div>
  );

  if (!step) return (
    <div className="container">
      <Header />
      <div className="error">Step not found. Please start over.</div>
      <div className="footer-actions" style={{ marginTop: '16px' }}>
        <button onClick={() => navigate('/')}>Back to Home</button>
      </div>
    </div>
  );

  return (
    <div className="container">
      <Header />
      <h2>{sessionState.flowName}</h2>
      <h3>{step.question}</h3>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        {step.options.map((option) => (
          <label key={option.value} className="option">
            <div>
              <input
                type="radio"
                name="choice"
                value={option.value}
                checked={selected === option.value}
                onChange={() => setSelected(option.value)}
              />
              <span className="option-label">{option.value}</span>
            </div>
            {option.description && (
              <div className="option-description">{option.description}</div>
            )}
          </label>
        ))}
        <div className="footer-actions">
          <button type="submit" disabled={submitting}>
            {submitting ? 'Loading…' : 'Continue'}
          </button>
          <button
            type="button"
            className="glass"
            onClick={() => navigate('/')}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
