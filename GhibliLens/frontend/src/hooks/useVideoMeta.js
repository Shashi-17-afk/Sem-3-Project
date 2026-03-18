import { useState, useEffect } from 'react';

export function useVideoMeta(file) {
  const [duration, setDuration] = useState(null);
  const [objectUrl, setObjectUrl] = useState(null);

  useEffect(() => {
    if (!file) {
      setDuration(null);
      setObjectUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setObjectUrl(url);

    const video = document.createElement('video');
    video.preload = 'metadata';
    video.src = url;
    video.onloadedmetadata = () => {
      setDuration(video.duration);
    };

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [file]);

  return { duration, objectUrl };
}
