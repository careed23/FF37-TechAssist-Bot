import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header.jsx';

export default function CompletePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { resolved, flowName } = location.state ?? {};

  return (
    <div className="container">
      <Header />
      <h2>Session logged</h2>
      <p>
        {resolved
          ? `✅ Great news! The ${flowName} issue was resolved and logged for analytics.`
          : `⚠️ The session has been logged. Please follow escalation procedures for ${flowName}.`}
      </p>
      <div className="footer-actions">
        <button onClick={() => navigate('/')}>Troubleshoot another issue</button>
      </div>
    </div>
  );
}
