import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

export const uploadVideo = (formData, onUploadProgress) =>
  client.post('/api/v1/video/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  });

export const getJobStatus = (jobId) =>
  client.get(`/api/v1/jobs/${jobId}/status`);

export const getDownloadUrl = (jobId) =>
  `${BASE_URL}/api/v1/jobs/${jobId}/download`;

export const getPreviewUrl = (jobId) =>
  `${BASE_URL}/api/v1/jobs/${jobId}/preview`;

export const cancelJob = (jobId) =>
  client.delete(`/api/v1/jobs/${jobId}`);
