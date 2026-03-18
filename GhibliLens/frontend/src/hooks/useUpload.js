import { useState, useRef, useCallback } from 'react';
import { uploadVideo, getJobStatus } from '../api/client';

const POLL_INTERVAL = 2500; // ms

export function useUpload() {
  const [uploadPhase, setUploadPhase] = useState('idle'); // idle | uploading | processing | complete | failed
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobData, setJobData] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [error, setError] = useState(null);

  const pollRef = useRef(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startPolling = useCallback((jobId) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await getJobStatus(jobId);
        setJobStatus(data);

        if (data.status === 'complete') {
          stopPolling();
          setUploadPhase('complete');
        } else if (data.status === 'failed') {
          stopPolling();
          setUploadPhase('failed');
          setError(data.error || 'Processing failed. Please try again.');
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
    }, POLL_INTERVAL);
  }, []);

  const submit = useCallback(async (file, options = {}) => {
    setError(null);
    setUploadPhase('uploading');
    setUploadProgress(0);
    setJobData(null);
    setJobStatus(null);

    const formData = new FormData();
    formData.append('file', file);
    if (options.startTime != null) formData.append('start_time', options.startTime);
    if (options.endTime != null) formData.append('end_time', options.endTime);
    if (options.fps) formData.append('fps', options.fps);

    try {
      const { data } = await uploadVideo(formData, (evt) => {
        if (evt.total) {
          setUploadProgress(Math.round((evt.loaded / evt.total) * 100));
        }
      });
      setJobData(data);
      setUploadPhase('processing');
      startPolling(data.job_id);
    } catch (err) {
      setUploadPhase('failed');
      const msg = err.response?.data?.detail || err.message || 'Upload failed.';
      setError(msg);
    }
  }, [startPolling]);

  const reset = useCallback(() => {
    stopPolling();
    setUploadPhase('idle');
    setUploadProgress(0);
    setJobData(null);
    setJobStatus(null);
    setError(null);
  }, []);

  return { uploadPhase, uploadProgress, jobData, jobStatus, error, submit, reset };
}
