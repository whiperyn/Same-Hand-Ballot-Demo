import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function SegmentedImages() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    fetch('http://localhost:8000/api/generated-images')
      .then(response => response.json())
      .then(data => {
        setImages(data.images);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching generated images:", error);
        setLoading(false);
      });
  }, []);

  const handleCalculateSimilarity = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/calculate-similarity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        navigate('/results');
      } else {
        console.error("Error calculating similarity");
      }
    } catch (error) {
      console.error("Error calculating similarity:", error);
    }
  };

  return (
    <div className="card">
      <div className="card-body">
        <h3 className="card-title">Segmented Images</h3>
        <p className="card-text">
          Below are the images generated from the segmentation process. Click <strong>Calculate Similarity</strong> to evaluate them further.
        </p>
        <button
          className="btn btn-success mb-3"
          onClick={handleCalculateSimilarity}
          disabled={loading || images.length === 0}
        >
          Calculate Similarity
        </button>

        {loading && <div className="alert alert-info">Loading images...</div>}

        <div className="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-3">
          {images.map((img, index) => (
            <div className="col" key={index}>
              <div className="card">
                <img
                  src={`http://localhost:8000/static/A/segmented_box/${img}`}
                  alt={`Segmented ${index}`}
                  className="card-img-top"
                  style={{ objectFit: 'contain', maxHeight: '200px' }}
                />
                <div className="card-body">
                  <p className="card-text text-center">{img}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SegmentedImages;
