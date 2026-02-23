import { useNavigate } from 'react-router-dom';

export default function Header() {
  const navigate = useNavigate();
  return (
    <header>
      <div className="brand">
        <div className="logo">
          <span>Forged Fiber</span>
          <span>37</span>
        </div>
        <div>
          <h1 className="app-title">FF37 TechAssist Bot</h1>
          <div className="subheading">Interactive Troubleshooting Assistant</div>
        </div>
      </div>
      <button className="glass" onClick={() => navigate('/')}>
        All Issues
      </button>
    </header>
  );
}
