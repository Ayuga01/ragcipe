import { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, Upload, RotateCcw, Scan, ImageIcon, CheckCircle2 } from 'lucide-react';
import { useCamera } from '../../hooks/useCamera';
import Button from '../common/Button';
import './CameraCapture.css';

export default function CameraCapture({ onCapture, onAnalyze, isAnalyzing }) {
  const [mode, setMode] = useState('idle'); // idle, camera, preview
  const [capturedImage, setCapturedImage] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);
  const { stream, error, startCamera, capturePhoto, stopCamera } = useCamera();
  const [success, setSuccess] = useState(false);
  const wasAnalyzing = useRef(false);

  useEffect(() => {
    if (isAnalyzing) {
      wasAnalyzing.current = true;
      setSuccess(false);
    } else if (wasAnalyzing.current && !isAnalyzing) {
      wasAnalyzing.current = false;
      setSuccess(true);
      const t = setTimeout(() => setSuccess(false), 1500);
      return () => clearTimeout(t);
    }
  }, [isAnalyzing]);

  useEffect(() => {
    if (stream && videoRef.current) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const handleStartCamera = async () => {
    try {
      await startCamera();
      setMode('camera');
    } catch {
      // error is handled by the hook
    }
  };

  const handleCapture = () => {
    const imageData = capturePhoto(videoRef);
    if (imageData) {
      setCapturedImage(imageData);
      stopCamera();
      setMode('preview');
      onCapture?.(imageData);
    }
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setMode('idle');
  };

  const handleFileUpload = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const imageData = e.target.result;
      setCapturedImage(imageData);
      setMode('preview');
      onCapture?.(imageData);
    };
    reader.readAsDataURL(file);
  }, [onCapture]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  return (
    <div className="camera-capture">
      {mode === 'idle' && (
        <div className="camera-capture__idle animate-fadeIn">
          <div className="camera-capture__options">
            <button className="camera-capture__option" onClick={handleStartCamera}>
              <div className="camera-capture__option-icon camera-capture__option-icon--camera">
                <Camera size={32} />
              </div>
              <span className="camera-capture__option-title">Open Camera</span>
              <span className="camera-capture__option-desc">Take a photo of your ingredients</span>
            </button>

            <div
              className={`camera-capture__dropzone ${dragActive ? 'camera-capture__dropzone--active' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={32} className="camera-capture__dropzone-icon" />
              <span className="camera-capture__option-title">Upload Image</span>
              <span className="camera-capture__option-desc">Drag & drop or click to browse</span>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => handleFileUpload(e.target.files[0])}
                hidden
              />
            </div>
          </div>
          {error && <p className="camera-capture__error">{error}</p>}
        </div>
      )}

      {mode === 'camera' && (
        <div className="camera-capture__camera animate-fadeIn">
          <div className="camera-capture__viewfinder">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="camera-capture__video"
            />
            <div className="camera-capture__corners">
              <span /><span /><span /><span />
            </div>
          </div>
          <div className="camera-capture__controls">
            <Button variant="ghost" onClick={() => { stopCamera(); setMode('idle'); }}>
              Cancel
            </Button>
            <button className="camera-capture__shutter" onClick={handleCapture}>
              <span className="camera-capture__shutter-inner" />
            </button>
            <div style={{ width: 72 }} />
          </div>
        </div>
      )}

      {mode === 'preview' && capturedImage && (
        <div className="camera-capture__preview animate-fadeIn">
          <div className="camera-capture__image-wrap">
            <img src={capturedImage} alt="Captured ingredients" className="camera-capture__image" />
            <div className="camera-capture__image-overlay">
              <ImageIcon size={20} />
              <span>Ready to analyze</span>
            </div>
          </div>
          <div className="camera-capture__actions">
            <Button variant="secondary" icon={RotateCcw} onClick={handleRetake}>
              Retake
            </Button>
            <Button 
              variant="primary" 
              icon={success ? CheckCircle2 : Scan} 
              loading={isAnalyzing}
              disabled={success || isAnalyzing}
              onClick={() => onAnalyze?.(capturedImage)}
              className={success ? 'btn--success' : ''}
              style={{ width: '220px', justifyContent: 'center' }}
            >
              {isAnalyzing ? 'Analyzing...' : success ? 'Detected!' : 'Analyze Ingredients'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
