import { useState, useCallback, useRef } from 'react';

export function useCamera() {
  const [stream, setStream] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState(null);
  const streamRef = useRef(null);

  const startCamera = useCallback(async (facingMode = 'environment') => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      streamRef.current = mediaStream;
      setStream(mediaStream);
      setIsActive(true);
      return mediaStream;
    } catch (err) {
      const message =
        err.name === 'NotAllowedError'
          ? 'Camera access denied. Please allow camera permissions.'
          : err.name === 'NotFoundError'
          ? 'No camera found on this device.'
          : `Camera error: ${err.message}`;
      setError(message);
      setIsActive(false);
      throw new Error(message);
    }
  }, []);

  const capturePhoto = useCallback((videoRef) => {
    if (!videoRef?.current) return null;

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL('image/jpeg', 0.85);
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setStream(null);
    setIsActive(false);
    setError(null);
  }, []);

  return {
    stream,
    isActive,
    error,
    startCamera,
    capturePhoto,
    stopCamera,
  };
}
