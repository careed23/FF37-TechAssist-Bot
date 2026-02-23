import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage.jsx';
import FlowStepPage from './pages/FlowStepPage.jsx';
import SolutionPage from './pages/SolutionPage.jsx';
import CompletePage from './pages/CompletePage.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/flow/:flowId/step/:stepId" element={<FlowStepPage />} />
        <Route path="/flow/:flowId/solution/:solutionId" element={<SolutionPage />} />
        <Route path="/complete" element={<CompletePage />} />
      </Routes>
    </BrowserRouter>
  );
}
