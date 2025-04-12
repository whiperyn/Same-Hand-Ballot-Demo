import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ImageAnnotation from './ImageAnnotation';
import SegmentedImages_A from './SegmentedImages_A';
import SegmentedImages_B from './SegmentedImages_B';
import Results from './Results';
import CombineImages from './CombineImages';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  return (
    <Router>
      <header>
        <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
          <div className="container">
            <Link to="/" className="navbar-brand">Same Hand Ballot</Link>
            <button
              className="navbar-toggler"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#navbarNav"
              aria-controls="navbarNav"
              aria-expanded="false"
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon" />
            </button>
            <div className="collapse navbar-collapse" id="navbarNav">
              <ul className="navbar-nav ms-auto">
                <li className="nav-item">
                  <Link to="/combine" className="nav-link">Combine Images</Link>
                </li>
                <li className="nav-item">
                  <Link to="/" className="nav-link">Annotate Image</Link>
                </li>
                <li className="nav-item">
                  <Link to="/segmentedA" className="nav-link">View Segmented Image A</Link>
                </li>
                <li className="nav-item">
                  <Link to="/segmentedB" className="nav-link">View Segmented Image B</Link>
                </li>
                <li className="nav-item">
                  <Link to="/results" className="nav-link">View Results</Link>
                </li>
              </ul>
            </div>
          </div>
        </nav>
      </header>

      <main className="py-4">
        <div className="container">
          <Routes>
            <Route path="/combine" element={<CombineImages />} />
            <Route path="/" element={<ImageAnnotation />} />
            <Route path="/segmentedA" element={<SegmentedImages_A />} />
            <Route path="/segmentedB" element={<SegmentedImages_B />} />
            <Route path="/results" element={<Results />} />
          </Routes>
        </div>
      </main>
    </Router>
  );
}

export default App;
