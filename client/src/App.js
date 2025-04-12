import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import AnnotationPanel from './AnnotationPanel';
import Results from './ResultsPanel';
import 'bootstrap/dist/css/bootstrap.min.css';

function Home() {
  const navigate = useNavigate();

  const handleCalculateSimilarity = async () => {
    try {
      await fetch('http://localhost:8000/api/calculate-similarity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      navigate('/results');
    } catch (err) {
      console.error('Error calculating similarity:', err);
    }
  };

  return (
    <div className="d-flex flex-column vh-100 bg-light">
      <div className="d-flex flex-grow-1 border-top border-bottom">
        <div className="w-50 border-end overflow-auto">
          <AnnotationPanel side="A" />
        </div>
        <div className="w-50 overflow-auto">
          <AnnotationPanel side="B" />
        </div>
      </div>
      <div className="border-top p-3 text-end bg-white">
        <button className="btn btn-lg btn-primary" onClick={handleCalculateSimilarity}>
          Calculate Similarity
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
        <Route path="/results" element={<Results />} />
      </Routes>
    </Router>
  );
}