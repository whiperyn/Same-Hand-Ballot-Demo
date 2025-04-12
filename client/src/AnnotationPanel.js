import React, { useRef, useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';

export default function AnnotationPanel({ side }) {
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const [image, setImage] = useState(null);
  const [picName, setPicName] = useState('');
  const [scaleFactor, setScaleFactor] = useState(1);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [boxes, setBoxes] = useState([]);
  const [points, setPoints] = useState([]);
  const [mode, setMode] = useState('box');
  const [thumbnails, setThumbnails] = useState([]);
  const [loadingSegments, setLoadingSegments] = useState(false);
  const [cacheCleared, setCacheCleared] = useState(false);
  const MAX_WIDTH = 800;

  const getMousePos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const drawCanvas = () => {
    if (!image) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, image.width * scaleFactor, image.height * scaleFactor);
    boxes.forEach(([x1, y1, x2, y2], idx) => {
      ctx.beginPath();
      ctx.rect(x1 * scaleFactor, y1 * scaleFactor, (x2 - x1) * scaleFactor, (y2 - y1) * scaleFactor);
      ctx.strokeStyle = 'red';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = 'red';
      ctx.font = 'bold 22px Arial';
      ctx.fillText(idx, x1 * scaleFactor + 4, y1 * scaleFactor + 16);
    });
    points.forEach(([[x, y]], idx) => {
      ctx.beginPath();
      ctx.arc(x * scaleFactor, y * scaleFactor, 5, 0, 2 * Math.PI);
      ctx.fillStyle = 'blue';
      ctx.fill();
      ctx.font = 'bold 22px Arial';
      ctx.fillText(idx, x * scaleFactor + 8, y * scaleFactor - 8);
    });
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('image', file);
    fetch('http://localhost:8000/api/upload-image', {
      method: 'POST',
      body: formData,
    })
      .then(res => res.json())
      .then(data => {
        setPicName(data.filename);
        const reader = new FileReader();
        reader.onload = (event) => {
          const img = new Image();
          img.onload = () => {
            const scale = Math.min(MAX_WIDTH / img.width, 1);
            setScaleFactor(scale);
            canvasRef.current.width = img.width * scale;
            canvasRef.current.height = img.height * scale;
            setImage(img);
          };
          img.src = event.target.result;
        };
        reader.readAsDataURL(file);
      });
  };

  const handleMouseDown = (e) => {
    const pos = getMousePos(e);
    if (mode === 'box') {
      setStartPos(pos);
      setIsDrawing(true);
    } else if (mode === 'point') {
      const newPoint = [[pos.x / scaleFactor, pos.y / scaleFactor]];
      setPoints(prev => [...prev, newPoint]);
      drawCanvas();
    }
  };

  const handleMouseUp = (e) => {
    if (!isDrawing || mode !== 'box') return;
    const pos = getMousePos(e);
    setIsDrawing(false);
    const x1 = Math.min(startPos.x, pos.x);
    const y1 = Math.min(startPos.y, pos.y);
    const x2 = Math.max(startPos.x, pos.x);
    const y2 = Math.max(startPos.y, pos.y);
    const newBox = [x1 / scaleFactor, y1 / scaleFactor, x2 / scaleFactor, y2 / scaleFactor];
    setBoxes(prev => [...prev, newBox]);
  };

  const handleMouseMove = (e) => {
    if (!isDrawing || mode !== 'box') return;
    drawCanvas();
    const ctx = canvasRef.current.getContext('2d');
    const pos = getMousePos(e);
    const x1 = Math.min(startPos.x, pos.x);
    const y1 = Math.min(startPos.y, pos.y);
    const x2 = Math.max(startPos.x, pos.x);
    const y2 = Math.max(startPos.y, pos.y);
    ctx.beginPath();
    ctx.rect(x1, y1, x2 - x1, y2 - y1);
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 2;
    ctx.stroke();
  };

  const handleUndo = () => {
    if (mode === 'box') setBoxes(prev => prev.slice(0, -1));
    else if (mode === 'point') setPoints(prev => prev.slice(0, -1));
  };

  const handleReset = () => {
    setBoxes([]);
    setPoints([]);
    setThumbnails([]);
    setPicName('');
    setImage(null);
    if (fileInputRef.current) fileInputRef.current.value = null;
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  const handleClearCache = async () => {
    await fetch('http://localhost:8000/api/clear-cache', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    setThumbnails([]);
    setCacheCleared(true);
    setTimeout(() => setCacheCleared(false), 3000);
  };

  const handleSegment = (type) => {
    const url = type === 'box' ? 'save-boxes' : 'save-points';
    const payload = {
      picName,
      [type === 'box' ? 'boxes' : 'points']: type === 'box' ? boxes : points,
    };
    fetch(`http://localhost:8000/api/${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(() => {
        setLoadingSegments(true);
        pollForThumbnails();
      });
  };

  const pollForThumbnails = () => {
    let elapsed = 0;
    const intervalId = setInterval(() => {
      elapsed += 3000;
      if (elapsed > 60000) {
        clearInterval(intervalId);
        setLoadingSegments(false);
        return;
      }
      fetch(`http://localhost:8000/api/generated-image${side}`)
        .then(res => res.json())
        .then(data => {
          if (data.images && data.images.length > 0) {
            setThumbnails(data.images);
            setLoadingSegments(false);
            clearInterval(intervalId);
          }
        })
        .catch(err => {
          console.error("Error checking segmented images:", err);
        });
    }, 3000);
  };

  useEffect(() => {
    drawCanvas();
  }, [image, boxes, points]);

  return (
    <div className="d-flex h-100 p-2 gap-2">
      <div className="w-75 d-flex flex-column">
        <div className="d-flex flex-wrap gap-2 mb-2 align-items-center">
          <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageUpload} className="form-control w-auto" />
          <div className="btn-group" role="group">
            <button onClick={() => setMode('box')} className={`btn ${mode === 'box' ? 'btn-primary' : 'btn-outline-primary'}`}>Box Mode</button>
            <button onClick={() => setMode('point')} className={`btn ${mode === 'point' ? 'btn-success' : 'btn-outline-success'}`}>Point Mode</button>
          </div>
          <button
            onClick={handleUndo}
            disabled={(mode === 'box' && boxes.length === 0) || (mode === 'point' && points.length === 0)}
            className="btn btn-outline-secondary"
          >
            Undo
          </button>
          <button onClick={handleReset} className="btn btn-outline-secondary">Reset</button>
          <button onClick={handleClearCache} className="btn btn-outline-danger">Clear Cache</button>
          <button onClick={() => handleSegment('box')} disabled={!picName || boxes.length === 0} className="btn btn-outline-primary">Segment (Boxes)</button>
          <button onClick={() => handleSegment('point')} disabled={!picName || points.length === 0} className="btn btn-outline-success">Segment (Points)</button>
        </div>
        {cacheCleared && (
          <div className="alert alert-info py-1 px-2 mb-2" role="alert">
            Cache cleared successfully.
          </div>
        )}
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          className="border border-dark rounded shadow bg-white flex-grow-1"
        />
      </div>
      <div className="w-25 ps-3 border-start overflow-auto">
        <h5>Segmented Results ({side})</h5>
        {loadingSegments ? (
          <div className="d-flex align-items-center text-muted">
            <div className="spinner-border spinner-border-sm me-2" role="status"></div>
            Segmenting image, please wait...
          </div>
        ) : (
          <div className="d-flex flex-column gap-2">
            {thumbnails.map((img, idx) => (
              <img
                key={idx}
                src={`http://localhost:8000/static/${side}/segmented_box/${img}`}
                alt={`Segment ${idx}`}
                className="img-fluid rounded border"
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}