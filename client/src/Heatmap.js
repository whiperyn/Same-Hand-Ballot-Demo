import React, { useEffect, useState, useMemo } from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

/* ================================
   Utility Functions for Score Mode
   ================================ */

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

function colorForScore(cellValue, lowMin) {
  if (!cellValue || cellValue.score === null) return 'grey';
  const score = Number(cellValue.score);

  if (score >= 0.1) {
    const factorHigh = (score - 0.1) / 0.9;
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

function colorForLogit(cellValue, stat) {
  if (!cellValue || cellValue.logit === null) return 'grey';
  const logit = Number(cellValue.logit);
  let factor = 0;
  if (stat.max !== stat.min) {
    factor = (logit - stat.min) / (stat.max - stat.min);
  }
  const red = Math.floor(255 - factor * (255 - 0));
  const green = Math.floor(255 - factor * (255 - 119));
  const blue = Math.floor(255 - factor * (255 - 182));
  return `rgb(${red}, ${green}, ${blue})`;
}

/* ================================
   Main Component
   ================================ */

function HeatmapChart() {
  const [heatmapData, setHeatmapData] = useState(null);
  const [lowRange, setLowRange] = useState({ lowMin: 0, lowMax: 0.01 });
  const [logitStats, setLogitStats] = useState({});
  const [colorMode, setColorMode] = useState("logit"); 
  const [displayMode, setDisplayMode] = useState("score"); 
  const navigate = useNavigate();

  useEffect(() => {
    fetch('http://localhost:8000/api/heatmap-data')
      .then((response) => response.json())
      .then((data) => {
        setHeatmapData(data);
        setLowRange(computeLowRange(data));
        const computedStats = {};
        data.queryKeys.forEach((query) => {
          let minL = Infinity;
          let maxL = -Infinity;
          data.data.forEach((row) => {
            const cell = row.columns.find((c) => c.queryKey === query);
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

  const rowsToDisplay = useMemo(() => {
    if (!heatmapData || !heatmapData.queryKeys) {
      return [];
    }
    if (heatmapData.queryKeys.length === 1) {
      const singleQuery = heatmapData.queryKeys[0];
      const filtered = heatmapData.data.filter((row) => row.poolKey !== singleQuery);
      filtered.sort((a, b) => {
        const getValue = (row) => {
          const cell = row.columns.find((c) => c.queryKey === singleQuery);
          if (cell && cell.score) {
            if (displayMode === "score" && cell.score.score != null) {
              return Number(cell.score.score);
            } else if (displayMode === "logit" && cell.score.logit != null) {
              return Number(cell.score.logit);
            }
          }
          return -Infinity;
        };
        return getValue(b) - getValue(a);
      });
      return filtered;
    }
    return heatmapData.data;
  }, [heatmapData, displayMode]);

  if (!heatmapData) {
    return (
      <div className="container text-center mt-5">
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">Loading...</span>
        </div>
      </div>
    );
  }

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
                headers: { 'Content-Type': 'application/json' },
              });

              if (response.ok) {
                console.log('✅ Files successfully copied.');
                navigate('/');
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

      <div className="table-responsive">
        {/* We force a fixed table layout so that the first column can remain small. */}
        <table
          className="table table-bordered table-hover table-sm"
          style={{ tableLayout: 'fixed', width: '100%' }}
        >
          <thead className="thead-light">
            <tr>
              <th
                className="text-center"
                style={{
                  backgroundColor: '#FC8C3B',
                  color: '#fff',
                  width: '120px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
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
            {rowsToDisplay.map((row) => (
              <tr key={row.poolKey}>
                <th
                  className="text-center align-middle"
                  style={{
                    backgroundColor: '#FC8C3B',
                    color: '#fff',
                    width: '120px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                >
                  {row.poolKey}
                </th>
                {row.columns.map((cell) => {
                  let displayedValue = '';
                  let cellColor = '';
                  if (colorMode === "score") {
                    cellColor = colorForScore(cell.score, lowRange.lowMin);
                  } else {
                    const stat = logitStats[cell.queryKey] || { min: 0, max: 1 };
                    cellColor = colorForLogit(cell.score, stat);
                  }
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
                          minWidth: '60px',
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
