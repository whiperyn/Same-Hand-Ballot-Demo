import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import AnnotationPanel from './AnnotationPanel';
import HeatMapChart from './Heatmap';
import Ranking from './Ranking';

function Home() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleCalculateSimilarity = async () => {
    try {
      setIsLoading(true);
      await fetch('http://localhost:8000/api/calculate-similarity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      navigate('/HeatmapChart');
    } catch (err) {
      console.error('Error calculating similarity:', err);
      setIsLoading(false);
    }
  };

  return (
    <div className="d-flex flex-column vh-100 bg-light">
      <div className="d-flex flex-grow-1 border-top border-bottom">
        <div className="border-end overflow-auto">
          <AnnotationPanel side="Query" />
        </div>
      </div>
      <div className="border-top p-3 text-end bg-white">
        <button
          className="btn btn-lg btn-primary"
          onClick={handleCalculateSimilarity}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Calculating...
            </>
          ) : (
            'Calculate Similarity'
          )}
        </button>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/HeatmapChart" element={<HeatMapChart />} />
        <Route path="/Ranking" element={<Ranking />} />
      </Routes>
    </Router>
  );
}
