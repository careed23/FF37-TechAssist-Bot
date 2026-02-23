import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header.jsx';
import { getFlows, getFlow } from '../api.js';

export default function HomePage() {
  const [flows, setFlows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [starting, setStarting] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getFlows()
      .then((data) => {
        setFlows(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleStart = async (flowId) => {
    setStarting(flowId);
    try {
      const flowData = await getFlow(flowId);
      navigate(`/flow/${flowId}/step/${flowData.first_step_id}`, {
        state: {
          flowName: flowData.name,
          startTime: new Date().toISOString(),
          stepsTaken: [],
        },
      });
    } catch (err) {
      setError(err.message);
      setStarting(null);
    }
  };

  if (loading) return (
    <div className="container">
      <Header />
      <p className="loading">Loading flows…</p>
    </div>
  );

  if (error) return (
    <div className="container">
      <Header />
      <div className="error">{error}</div>
    </div>
  );

  return (
    <div className="container">
      <Header />
      <h2>Select a troubleshooting scenario</h2>
      {flows.length === 0 ? (
        <p>No troubleshooting flows are available.</p>
      ) : (
        <ul className="flow-list">
          {flows.map((flow) => (
            <li key={flow.id} className="flow-card">
              <div>
                <div className="flow-title">{flow.name}</div>
                <p className="flow-description">{flow.description}</p>
              </div>
              <button
                onClick={() => handleStart(flow.id)}
                disabled={starting === flow.id}
              >
                {starting === flow.id ? 'Loading…' : 'Start'}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
