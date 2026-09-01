import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import SignalDetection from './pages/SignalDetection';
import AIAnalysis from './pages/AIAnalysis';
import DSPPipeline from './pages/DSPPipeline';
import BitStreamAnalysis from './pages/BitStreamAnalysis';
import { AnalysisProvider } from './context/AnalysisContext';
import './index.css';

// Placeholder for uncreated pages
const Placeholder = ({ title }) => (
  <div className="page-layout">
    <div className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--color-surface-container-lowest)' }}>
      <h1 className="font-headline-lg" style={{ color: 'var(--color-on-surface-variant)' }}>{title}</h1>
    </div>
  </div>
);

function App() {
  return (
    <AnalysisProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          
          <Route path="/signal-detection" element={<SignalDetection />} />
          <Route path="/ai-analysis" element={<AIAnalysis />} />
          <Route path="/dsp-pipeline" element={<DSPPipeline />} />
          <Route path="/bit-stream" element={<BitStreamAnalysis />} />
          
          <Route path="/upload" element={<Placeholder title="Upload Signal" />} />
          <Route path="/results" element={<Placeholder title="Results" />} />
          <Route path="/dataset" element={<Placeholder title="Dataset Generator" />} />
          <Route path="/model-training" element={<Placeholder title="Model Training" />} />
          <Route path="/settings" element={<Placeholder title="Settings" />} />
        </Routes>
      </BrowserRouter>
    </AnalysisProvider>
  );
}

export default App;
