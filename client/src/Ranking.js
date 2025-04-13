// src/Ranking.js
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useNavigate } from 'react-router-dom'; // Make sure this is imported


// Helper function to update image paths to point to the Flask server.
const transformImagePath = (path) => {
  // Convert relative image paths from backend (e.g., "./static/Query/...")
  // to absolute URLs hosted on your Flask server.
  return path.replace(/^\.\/static/, 'http://localhost:8000/static');
};

const Ranking = () => {
  const [rankingInfo, setRankingInfo] = useState(null);

    const navigate = useNavigate(); // Add this inside your component


  useEffect(() => {
    fetch('http://localhost:8000/api/ranking-data')
      .then((res) => res.json())
      .then((data) => setRankingInfo(data))
      .catch((err) => console.error('Error fetching ranking data:', err));
  }, []);

  if (!rankingInfo) {
    return (
      <div className="container my-5">
        <p>Loading ranking data...</p>
      </div>
    );
  }

  const { queryKeys, rankingData } = rankingInfo;

  // Define size limits for query images (left side) and pool images (right side)
  const queryImageStyle = {
    maxWidth: '150px',
    maxHeight: '150px',
    objectFit: 'contain',
    width: '100%', // ensure responsive scaling within the container
    height: 'auto'
  };

  const poolImageStyle = {
    maxWidth: '100px',
    maxHeight: '100px',
    objectFit: 'contain',
    width: '100%',
    height: 'auto'
  };

  // Container styles to enforce fixed dimensions.
  const queryImageContainer = {
    width: '150px',
    height: '150px',
    overflow: 'hidden'
  };

  const poolImageContainer = {
    width: '100px',
    height: '100px',
    overflow: 'hidden'
  };

  return (
    <div className="container my-4">
      <h2 className="mb-4">Ranking Visualization</h2>
      {queryKeys.map((queryKey) => {
        const poolList = rankingData[queryKey];

        if (!Array.isArray(poolList)) {
          console.error(`Expected poolList for ${queryKey} to be an array, but got:`, poolList);
          return (
            <div key={queryKey} className="alert alert-danger">
              Error: Invalid data for {queryKey}
            </div>
          );
        }

        // Get the query image from the first pool item.
        const rawQueryImage = poolList.length > 0 ? poolList[0].Query_path : '';
        const queryImage = rawQueryImage ? transformImagePath(rawQueryImage) : '';

        return (
          <div className="card mb-4" key={queryKey}>
            <div className="card-body">
              <div className="row align-items-center">
                {/* Left Column: Query key and image */}
                <div className="col-md-3 text-center">
                  <h5 className="card-title">{queryKey}</h5>
                  <div style={queryImageContainer} className="mx-auto mb-2">
                    {queryImage ? (
                      <img
                        src={queryImage}
                        alt={`Query ${queryKey}`}
                        className="img-fluid rounded"
                        style={queryImageStyle}
                      />
                    ) : (
                      <p>No image available</p>
                    )}
                  </div>
                </div>

                {/* Right Column: Pool Rankings Table */}
                <div className="col-md-9">
                  <table className="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Pool Key</th>
                        <th>Pool Image</th>
                        <th>Score</th>
                        <th>Logit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {poolList.slice(0, 5).map((item, idx) => {
                        const poolImage = transformImagePath(item.Pool_path);
                        return (
                          <tr key={idx}>
                            <td>{idx + 1}</td>
                            <td>{item.Pool}</td>
                            <td>
                              <div style={poolImageContainer} className="mx-auto">
                                <img
                                  src={poolImage}
                                  alt={`Pool ${item.Pool}`}
                                  className="img-fluid rounded"
                                  style={poolImageStyle}
                                />
                              </div>
                            </td>
                            <td>{item.Score}</td>
                            <td>{item.Logit}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        );
      })}

      {/* Bottom-right navigation buttons */}
      <div className="d-flex justify-content-end">
        <Link to="/HeatmapChart" className="btn btn-secondary me-2">
          Go Back to Heatmap
        </Link>
        <button
            className="btn btn-primary"
            onClick={async () => {
                try {
                const response = await fetch('http://localhost:8000/api/copy-irregular', {
                    method: 'POST',
                    headers: {
                    'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    console.log('✅ Files successfully copied.');
                    navigate('/'); // Navigate after successful copy
                } else {
                    console.error('❌ Failed to copy files.');
                }
                } catch (error) {
                console.error('🚨 Error while copying files:', error);
                }
            }}
            >
            Finish
        </button>

      </div>
    </div>
  );
};

export default Ranking;
