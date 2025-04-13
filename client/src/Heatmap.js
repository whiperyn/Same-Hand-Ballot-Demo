import React, { useEffect, useState } from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';


/* ================================
   Utility Functions for Score Mode
   ================================ */

/**
 * Computes the domain for cells in the low score range (score < 0.01)
 * across the entire table.
 */
function computeLowRange(heatmapData) {
  let lowMin = Infinity;
  let lowMax = -Infinity;
  heatmapData.data.forEach((row) => {
    row.columns.forEach((cell) => {
      if (cell.score && cell.score.score !== null) {
        const s = Number(cell.score.score);
        if (s < 0.01) {
          if (s < lowMin) lowMin = s;
          if (s > lowMax) lowMax = s;
        }
      }
    });
  });
  if (lowMin === Infinity || lowMax === -Infinity) {
    lowMin = 0;
    lowMax = 0.01;
  }
  return { lowMin, lowMax };
}

/**
 * Returns a color for score mode.
 * Uses three ranges:
 *  - High (score ≥ 0.1): interpolate from #00b4d8 (0,180,216) to #0077b6 (0,119,182)
 *  - Medium (0.01 ≤ score < 0.1): interpolate from #ade8f4 (173,232,244) to #48cae4 (72,202,228)
 *  - Low (score < 0.01): interpolate from white (#ffffff) to a stronger light blue (#91b0ed → 145,176,237)
 * Diagonal or missing cells return grey.
 */
function colorForScore(cellValue, lowMin) {
  if (!cellValue || cellValue.score === null) return 'grey';
  const score = Number(cellValue.score);

  if (score >= 0.1) {
    const factorHigh = (score - 0.1) / 0.9; // normalized: 0 at 0.1, 1 at 1.0
    const red = 0;
    const green = Math.floor(180 - factorHigh * (180 - 119));
    const blue = Math.floor(216 - factorHigh * (216 - 182));
    return `rgb(${red}, ${green}, ${blue})`;
  } else if (score >= 0.01) {
    const factorMed = (score - 0.01) / 0.09;
    const red = Math.floor(173 - factorMed * (173 - 72));
    const green = Math.floor(232 - factorMed * (232 - 202));
    const blue = Math.floor(244 - factorMed * (244 - 228));
    return `rgb(${red}, ${green}, ${blue})`;
  } else {
    const denom = (0.01 - lowMin) || 1;
    const factorLow = (score - lowMin) / denom;
    const red = Math.floor(255 - factorLow * (255 - 145));
    const green = Math.floor(255 - factorLow * (255 - 176));
    const blue = Math.floor(255 - factorLow * (255 - 237));
    return `rgb(${red}, ${green}, ${blue})`;
  }
}

/* ================================
   Utility Function for Logit Mode
   ================================ */

/**
 * Returns a color for logit mode.
 * For each query (column), the minimum logit maps to white (255,255,255)
 * and the maximum maps to blue (#0077b6 → RGB: 0,119,182) using linear interpolation.
 */
function colorForLogit(cellValue, stat) {
  if (!cellValue || cellValue.logit === null) return 'grey';
  const logit = Number(cellValue.logit);
  let factor = 0;
  if (stat.max !== stat.min) {
    factor = (logit - stat.min) / (stat.max - stat.min);
  }
  const red = Math.floor(255 - factor * (255 - 0));         // 255 -> 0
  const green = Math.floor(255 - factor * (255 - 119));      // 255 -> 119
  const blue = Math.floor(255 - factor * (255 - 182));       // 255 -> 182
  return `rgb(${red}, ${green}, ${blue})`;
}

/* ================================
   Main Component
   ================================ */

function HeatmapChart() {
  // heatmapData is the full object from the backend.
  const [heatmapData, setHeatmapData] = useState(null);
  const [lowRange, setLowRange] = useState({ lowMin: 0, lowMax: 0.01 });
  const [logitStats, setLogitStats] = useState({}); // Object keyed by query
  // Two separate toggles:
  // colorMode controls which metric is used for cell coloring.
  // displayMode controls which value is shown in the cells.
  const [colorMode, setColorMode] = useState("score"); // "score" or "logit"
  const [displayMode, setDisplayMode] = useState("score"); // "score" or "logit"
  const navigate = useNavigate();


  useEffect(() => {
    fetch('http://localhost:8000/api/heatmap-data')
      .then(response => response.json())
      .then(data => {
        setHeatmapData(data);
        setLowRange(computeLowRange(data));
        // Compute logitStats for each query (column) independently.
        const computedStats = {};
        data.queryKeys.forEach((query) => {
          let minL = Infinity;
          let maxL = -Infinity;
          data.data.forEach((row) => {
            const cell = row.columns.find(c => c.queryKey === query);
            if (cell && cell.score && cell.score.logit != null) {
              const L = Number(cell.score.logit);
              if (L < minL) minL = L;
              if (L > maxL) maxL = L;
            }
          });
          if (minL === Infinity || maxL === -Infinity) {
            minL = 0;
            maxL = 1;
          }
          computedStats[query] = { min: minL, max: maxL };
        });
        setLogitStats(computedStats);
      });
  }, []);

  if (!heatmapData) {
    return (
      <div className="container text-center mt-5">
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">Loading...</span>
        </div>
      </div>
    );
  }

  // Toggle buttons for color mode and display mode are independent.
  const toggleColorMode = (
    <div className="btn-group mb-3 me-2">
      <span className="me-2">Color Mode:</span>
      <button
        type="button"
        className={`btn ${colorMode === "score" ? "btn-primary" : "btn-outline-primary"}`}
        onClick={() => setColorMode("score")}
      >
        Score
      </button>
      <button
        type="button"
        className={`btn ${colorMode === "logit" ? "btn-primary" : "btn-outline-primary"}`}
        onClick={() => setColorMode("logit")}
      >
        Logit
      </button>
    </div>
  );

  const toggleDisplayMode = (
    <div className="btn-group mb-3">
      <span className="me-2">Display Value:</span>
      <button
        type="button"
        className={`btn ${displayMode === "score" ? "btn-primary" : "btn-outline-primary"}`}
        onClick={() => setDisplayMode("score")}
      >
        Score
      </button>
      <button
        type="button"
        className={`btn ${displayMode === "logit" ? "btn-primary" : "btn-outline-primary"}`}
        onClick={() => setDisplayMode("logit")}
      >
        Logit
      </button>
    </div>
  );

  return (
    <div className="container mt-4">
        <div className="d-flex justify-content-end mb-2">
        <button
            className="btn btn-secondary"
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
                navigate('/'); // Redirect to Home
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

      <h2 className="text-center mb-4">Heatmap Chart</h2>
      
      <div className="d-flex flex-wrap justify-content-center">
        {toggleColorMode}
        {toggleDisplayMode}
      </div>

      {/* Legend stays the same 
      <div className="mb-3 text-center">
        <h6>Legend:</h6>
        <span
          style={{
            backgroundColor: '#00b4d8',
            padding: '5px 10px',
            borderRadius: '4px',
            marginRight: '5px',
            color: '#fff'
          }}
        >
          High (≥ 0.1)
        </span>
        <span
          style={{
            backgroundColor: '#ade8f4',
            padding: '5px 10px',
            borderRadius: '4px',
            marginRight: '5px'
          }}
        >
          Medium (0.01 - 0.1)
        </span>
        <span
          style={{
            backgroundColor: '#ffffff',
            padding: '5px 10px',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        >
          Low (&lt; 0.01)
        </span>
      </div>
        */}
      <div className="table-responsive">
        <table className="table table-bordered table-hover table-sm">
          <thead className="thead-light">
            <tr>
              <th
                className="text-center"
                style={{ backgroundColor: 'orange', color: '#fff' }}
              >
                Pool &#92; Query
              </th>
              {heatmapData.queryKeys.map((query) => (
                <th
                  key={query}
                  className="text-center"
                  style={{ backgroundColor: 'lightgreen' }}
                >
                  {query}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {heatmapData.data.map((row) => (
              <tr key={row.poolKey}>
                <th
                  className="text-center align-middle"
                  style={{ backgroundColor: 'orange', color: '#fff' }}
                >
                  {row.poolKey}
                </th>
                {row.columns.map((cell) => {
                  let displayedValue = '';
                  // Determine the cell color based on the selected color mode.
                  let cellColor = '';
                  if (colorMode === "score") {
                    cellColor = colorForScore(cell.score, lowRange.lowMin);
                  } else {
                    const stat = logitStats[cell.queryKey] || { min: 0, max: 1 };
                    cellColor = colorForLogit(cell.score, stat);
                  }
                  // Determine the displayed value based on the selected display mode.
                  if (displayMode === "score") {
                    displayedValue =
                      cell.score && cell.score.score != null
                        ? Number(cell.score.score).toFixed(4)
                        : '';
                  } else {
                    displayedValue =
                      cell.score && cell.score.logit != null
                        ? Number(cell.score.logit).toFixed(4)
                        : '';
                  }
                  return (
                    <OverlayTrigger
                      key={`tooltip-${row.poolKey}-${cell.queryKey}`}
                      placement="top"
                      overlay={
                        <Tooltip id={`tooltip-${row.poolKey}-${cell.queryKey}`}>
                          <div>
                            <strong>Query:</strong> {cell.queryKey}
                          </div>
                          <div>
                            <strong>Pool:</strong> {row.poolKey}
                          </div>
                          <div>
                            <strong>Score:</strong>{' '}
                            {cell.score && cell.score.score !== null
                              ? Number(cell.score.score).toFixed(4)
                              : 'N/A'}
                          </div>
                          <div>
                            <strong>Logit:</strong>{' '}
                            {cell.score && cell.score.logit !== null
                              ? Number(cell.score.logit).toFixed(4)
                              : 'N/A'}
                          </div>
                        </Tooltip>
                      }
                    >
                      <td
                        className="align-middle heatmap-cell"
                        style={{
                          backgroundColor: cellColor,
                          minWidth: '70px',
                          textAlign: 'center',
                          cursor: 'pointer'
                        }}
                      >
                        {displayedValue}
                      </td>
                    </OverlayTrigger>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ position: 'fixed', bottom: '20px', right: '20px' }}>
        <button className="btn btn-primary" onClick={() => navigate('/ranking')}>
        See Ranking
        </button>
    </div>
    </div>
  );
}

export default HeatmapChart;
