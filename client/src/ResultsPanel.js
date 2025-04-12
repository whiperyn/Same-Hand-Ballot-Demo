import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function ResultsPanel() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('http://localhost:8000/api/result')
      .then(response => {
        if (!response.ok) {
          throw new Error("Network response was not OK");
        }
        return response.json();
      })
      .then(data => {
        setResult(data);
      })
      .catch(error => {
        console.error("Error fetching result:", error);
        setError(error.message);
      });
  }, []);

  return (
    <div className="container mt-4">
      <div className="card">
        <div className="card-body">
          <h3 className="card-title">Similarity Results</h3>
          {error && (
            <div className="alert alert-danger" role="alert">
              Error: {error}
            </div>
          )}
          {!error && !result && (
            <div className="alert alert-info" role="alert">
              Loading results...
            </div>
          )}
          {result && (
            <div className="p-3 mb-2 bg-light border rounded">
              <p><strong>Similarity 1:</strong> {result.similarity1}</p>
              <p><strong>Similarity 2:</strong> {result.similarity2}</p>
              <p><strong>Similarity 3:</strong> {result.similarity3}</p>
              <hr />
              <p><strong>Overall Similarity:</strong> {result.overall_similarity}</p>
            </div>
          )}
          <button className="btn btn-secondary mt-3" onClick={() => navigate('/')}>Go Back</button>
        </div>
      </div>
    </div>
  );
}

export default ResultsPanel;