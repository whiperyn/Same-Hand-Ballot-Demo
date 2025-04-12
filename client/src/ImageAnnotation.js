import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function ImageAnnotation() {
  const canvasRef = useRef(null);
  const navigate = useNavigate();
  const [image, setImage] = useState(null);
  const [boxes, setBoxes] = useState([]);
  const [points, setPoints] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [scaleFactor, setScaleFactor] = useState(1);
  const [picName, setPicName] = useState('');
  const [processing, setProcessing] = useState(false);
  const [combinedImageName, setCombinedImageName] = useState(null);
  const [annotationMode, setAnnotationMode] = useState('box');

  const MAX_WIDTH = 800;

  useEffect(() => {
    fetch('http://localhost:8000/api/get-combined-image')
      .then(res => res.json())
      .then(data => {
        setCombinedImageName(data.combinedImageName);
      })
      .catch(err => {
        console.error("Error fetching combined image:", err);
        setCombinedImageName(null);
      });
  }, []);

  const getMousePos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
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
      .then((response) => response.json())
      .then((data) => {
        setPicName(data.filename);
        const reader = new FileReader();
        reader.onload = (event) => {
          const img = new Image();
          img.onload = () => {
            const scale = Math.min(MAX_WIDTH / img.width, 1);
            setScaleFactor(scale);
            const canvas = canvasRef.current;
            canvas.width = img.width * scale;
            canvas.height = img.height * scale;
            drawCanvas(img, boxes, scale, points);
          };
          img.src = event.target.result;
          setImage(img);
        };
        reader.readAsDataURL(file);
      })
      .catch((error) => {
        console.error("Error uploading file:", error);
      });
  };

  const drawCanvas = (img, boxesArray = boxes, scale = scaleFactor, pointsArray = points) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (img) ctx.drawImage(img, 0, 0, img.width * scale, img.height * scale);

    boxesArray.forEach(([x1, y1, x2, y2], index) => {
      const scaledX1 = x1 * scale;
      const scaledY1 = y1 * scale;
      const scaledX2 = x2 * scale;
      const scaledY2 = y2 * scale;

      ctx.beginPath();
      ctx.rect(scaledX1, scaledY1, scaledX2 - scaledX1, scaledY2 - scaledY1);
      ctx.lineWidth = 2;
      ctx.strokeStyle = "red";
      ctx.stroke();

      ctx.fillStyle = "red";
      ctx.font = "16px Arial";
      ctx.fillText(index, scaledX1 + 4, scaledY1 + 18);
    });

    pointsArray.forEach(([[x, y]], index) => {
      const scaledX = x * scale;
      const scaledY = y * scale;

      ctx.beginPath();
      ctx.arc(scaledX, scaledY, 5, 0, 2 * Math.PI);
      ctx.fillStyle = 'blue';
      ctx.fill();

      ctx.fillStyle = "blue";
      ctx.font = "16px Arial";
      ctx.fillText(index, scaledX + 8, scaledY - 8);
    });
  };

  const handleMouseDown = (e) => {
    const pos = getMousePos(e);
    if (annotationMode === 'box') {
      setStartPos(pos);
      setIsDrawing(true);
    } else if (annotationMode === 'point') {
      const newPoint = [[pos.x / scaleFactor, pos.y / scaleFactor]];
      const updatedPoints = [...points, newPoint];
      setPoints(updatedPoints);
      drawCanvas(image, boxes, scaleFactor, updatedPoints);
    }
  };

  const handleMouseMove = (e) => {
    if (!isDrawing || annotationMode !== 'box') return;
    const pos = getMousePos(e);
    const x1 = Math.min(startPos.x, pos.x);
    const y1 = Math.min(startPos.y, pos.y);
    const x2 = Math.max(startPos.x, pos.x);
    const y2 = Math.max(startPos.y, pos.y);
    drawCanvas(image, boxes, scaleFactor, points);
    const ctx = canvasRef.current.getContext('2d');
    ctx.beginPath();
    ctx.rect(x1, y1, x2 - x1, y2 - y1);
    ctx.lineWidth = 2;
    ctx.strokeStyle = "red";
    ctx.stroke();
  };

  const handleMouseUp = (e) => {
    if (!isDrawing || annotationMode !== 'box') return;
    setIsDrawing(false);
    const pos = getMousePos(e);
    const x1 = Math.min(startPos.x, pos.x);
    const y1 = Math.min(startPos.y, pos.y);
    const x2 = Math.max(startPos.x, pos.x);
    const y2 = Math.max(startPos.y, pos.y);
    const newBox = [x1 / scaleFactor, y1 / scaleFactor, x2 / scaleFactor, y2 / scaleFactor];
    const updatedBoxes = [...boxes, newBox];
    setBoxes(updatedBoxes);
    drawCanvas(image, updatedBoxes, scaleFactor, points);
  };

  const handleUndo = () => {
    if (annotationMode === 'box') {
      const updatedBoxes = boxes.slice(0, -1);
      setBoxes(updatedBoxes);
      drawCanvas(image, updatedBoxes, scaleFactor, points);
    } else if (annotationMode === 'point') {
      const updatedPoints = points.slice(0, -1);
      setPoints(updatedPoints);
      drawCanvas(image, boxes, scaleFactor, updatedPoints);
    }
  };

  const handleSegmentation = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/save-boxes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ boxes, picName }),
      });
      if (response.ok) {
        setProcessing(true);
      } else {
        console.error("Failed to send boxes and picName");
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const handlePointSegmentation = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/save-points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points, picName }),
      });
      if (response.ok) {
        setProcessing(true);
      } else {
        console.error("Failed to send points and picName");
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const handleUseCombinedImage = () => {
    if (!combinedImageName) return;
    const url = `http://localhost:8000/uploads/${combinedImageName}`;
    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.onload = () => {
      const scale = Math.min(MAX_WIDTH / img.width, 1);
      setScaleFactor(scale);
      const canvas = canvasRef.current;
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      drawCanvas(img, [], scale, []);
      setImage(img);
      setPicName(combinedImageName);
      setBoxes([]);
      setPoints([]);
    };
    img.src = url;
  };

  const handleClearCache = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/clear-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) alert("Cache cleared successfully!");
      else alert("Failed to clear cache.");
    } catch (error) {
      console.error("Error clearing cache:", error);
      alert("Error clearing cache.");
    }
  };

  useEffect(() => {
    let intervalId;
    if (processing) {
      intervalId = setInterval(() => {
        fetch('http://localhost:8000/api/check-segmentation-status')
          .then((res) => res.json())
          .then((data) => {
            if (data.segmentedB) {
              clearInterval(intervalId);
              setProcessing(false);
              navigate('/segmentedB');
            } else if (data.segmentedA) {
              clearInterval(intervalId);
              setProcessing(false);
              navigate('/segmentedA');
            }
          })
          .catch((error) => {
            console.log("Segmentation status not ready yet...", error);
          });
      }, 3000);
    }
    return () => clearInterval(intervalId);
  }, [processing, navigate]);

  useEffect(() => {
    drawCanvas(image, boxes, scaleFactor, points);
  }, [image, boxes, points, scaleFactor]);

  return (
    <div className="card my-3">
      <div className="card-body">
        <h3 className="card-title">Annotate Image</h3>
        <p className="card-text">Upload an image and annotate using boxes or points, then click segment.</p>
        <div className="mb-3">
          <label className="form-label"><strong>Select Image:</strong></label>
          <input className="form-control" type="file" accept="image/*" onChange={handleImageUpload} />
        </div>
        <div className="mb-3">
          <button className="btn btn-outline-primary me-2" onClick={() => setAnnotationMode('box')}>
            Box Mode
          </button>
          <button className="btn btn-outline-success me-2" onClick={() => setAnnotationMode('point')}>
            Point Mode
          </button>
        </div>
        <div className="mb-3">
          <button className="btn btn-secondary me-2" onClick={handleUndo} disabled={boxes.length + points.length === 0}>
            Undo Last
          </button>
          <button className="btn btn-primary me-2" onClick={handleSegmentation} disabled={!picName || boxes.length === 0}>
            Segment (Boxes)
          </button>
          <button className="btn btn-warning me-2" onClick={handlePointSegmentation} disabled={!picName || points.length === 0}>
            Segment (Points)
          </button>
          <button className="btn btn-info me-2" onClick={handleUseCombinedImage} disabled={!combinedImageName}>
            Use Combined Image
          </button>
          <button className="btn btn-danger" onClick={handleClearCache}>
            Remove Cache
          </button>
        </div>
        <div className="row">
          <div className="col-md-8">
            <canvas
              ref={canvasRef}
              style={{ border: '1px solid #ccc', cursor: 'crosshair', width: '100%', height: 'auto' }}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            />
          </div>
          <div className="col-md-4">
            <h5>Recorded Boxes</h5>
            <pre style={{ background: '#f8f9fa', padding: '10px' }}>{JSON.stringify(boxes, null, 2)}</pre>
            <h5>Recorded Points</h5>
            <pre style={{ background: '#f8f9fa', padding: '10px' }}>{JSON.stringify(points, null, 2)}</pre>
          </div>
        </div>
      </div>
      {processing && (
        <div className="modal" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content p-4 text-center">
              <h5>Segmenting Image, please wait...</h5>
              <div className="progress mt-3">
                <div className="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style={{ width: '100%' }}></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ImageAnnotation;
