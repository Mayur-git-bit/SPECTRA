import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'smartsignal.analysisBundle';
const AnalysisContext = createContext(null);

function readStoredBundle() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AnalysisProvider({ children }) {
  const [analysisBundle, setAnalysisBundleState] = useState(() => readStoredBundle());

  const setAnalysisBundle = (bundle) => {
    setAnalysisBundleState(bundle);
    try {
      if (bundle) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(bundle));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Ignore storage failures and keep in-memory state.
    }
  };

  useEffect(() => {
    if (!analysisBundle) {
      const stored = readStoredBundle();
      if (stored) {
        setAnalysisBundleState(stored);
      }
    }
  }, []);

  const value = useMemo(() => ({ analysisBundle, setAnalysisBundle }), [analysisBundle]);

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
}
