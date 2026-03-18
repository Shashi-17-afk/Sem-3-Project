import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import UploadZone from './components/UploadZone';
import VideoTrimmer from './components/VideoTrimmer';
import ProgressBar from './components/ProgressBar';
import ComparePlayer from './components/ComparePlayer';
import DownloadButton from './components/DownloadButton';
import { useUpload } from './hooks/useUpload';
import { useVideoMeta } from './hooks/useVideoMeta';
import './styles/index.css';

const MAX_DURATION = 15;

export default function App() {
  const [file, setFile] = useState(null);
  const [trimRange, setTrimRange] = useState([0, 15]);
  const { duration, objectUrl } = useVideoMeta(file);
  const { uploadPhase, uploadProgress, jobData, jobStatus, error, submit, reset } = useUpload();

  const needsTrim = duration != null && duration > MAX_DURATION;
  const isIdle = uploadPhase === 'idle';
  const isActive = uploadPhase === 'uploading' || uploadPhase === 'processing';
  const isDone = uploadPhase === 'complete';
  const isFailed = uploadPhase === 'failed';

  const handleFileSelected = (f) => {
    setFile(f);
    setTrimRange([0, Math.min(MAX_DURATION, f.duration || MAX_DURATION)]);
  };

  const handleTrimChange = (start, end) => setTrimRange([start, end]);

  const handleSubmit = () => {
    if (!file) return;
    const opts = needsTrim
      ? { startTime: trimRange[0], endTime: trimRange[1] }
      : {};
    submit(file, opts);
  };

  const handleReset = () => {
    setFile(null);
    setTrimRange([0, 15]);
    reset();
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app__header">
        <motion.h1
          className="app__logo"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          🌿 GhibliLens
        </motion.h1>
        <motion.p
          className="app__tagline"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
        >
          Transform your world into a Studio Ghibli masterpiece
        </motion.p>
      </header>

      <main className="app__main">
        <AnimatePresence mode="wait">

          {/* ─── IDLE / UPLOAD STATE ───────────────────────── */}
          {(isIdle || isActive) && !isDone && (
            <motion.div
              key="upload-panel"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -24 }}
              transition={{ duration: 0.4 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}
            >
              <div className="card">
                {!file ? (
                  <UploadZone onFileSelected={handleFileSelected} disabled={isActive} />
                ) : (
                  <>
                    {/* File chip */}
                    <div className="file-info">
                      <span className="file-info__icon">🎬</span>
                      <div>
                        <p className="file-info__name">{file.name}</p>
                        <p className="file-info__meta">
                          {(file.size / 1024 / 1024).toFixed(1)} MB
                          {duration != null && ` · ${duration.toFixed(1)}s`}
                        </p>
                      </div>
                      {isIdle && (
                        <button className="file-info__remove" onClick={handleReset}>✕</button>
                      )}
                    </div>

                    {/* Trimmer */}
                    {needsTrim && isIdle && (
                      <div style={{ marginTop: 16 }}>
                        <VideoTrimmer
                          duration={duration}
                          onChange={handleTrimChange}
                        />
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Progress */}
              {isActive && (
                <div className="card">
                  <ProgressBar
                    phase={uploadPhase}
                    uploadProgress={uploadProgress}
                    jobStatus={jobStatus}
                  />
                </div>
              )}

              {/* Error */}
              {isFailed && (
                <div className="error-box">
                  ⚠️ {error}
                </div>
              )}

              {/* Submit button */}
              {file && isIdle && (
                <motion.button
                  className="btn btn--primary"
                  onClick={handleSubmit}
                  disabled={needsTrim && trimRange[1] - trimRange[0] > MAX_DURATION}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  🪄 Paint my world in Ghibli style
                </motion.button>
              )}
            </motion.div>
          )}

          {/* ─── COMPLETE STATE ─────────────────────────────── */}
          {isDone && (
            <motion.div
              key="result-panel"
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}
            >
              <div className="card">
                <ComparePlayer
                  originalUrl={objectUrl}
                  ghibliUrl={`http://localhost:8000/api/v1/jobs/${jobData?.job_id}/download`}
                />
              </div>

              <div style={{ display: 'flex', gap: 12 }}>
                <DownloadButton jobId={jobData?.job_id} />
                <motion.button
                  className="btn btn--secondary"
                  onClick={handleReset}
                  whileHover={{ scale: 1.02 }}
                  style={{ flex: 1 }}
                >
                  🔄 Start over
                </motion.button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>
    </div>
  );
}
