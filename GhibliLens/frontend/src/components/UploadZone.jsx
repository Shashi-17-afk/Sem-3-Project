import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';

const MAX_SIZE = 100 * 1024 * 1024; // 100MB

export default function UploadZone({ onFileSelected, disabled }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) onFileSelected(acceptedFiles[0]);
  }, [onFileSelected]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.mov', '.webm', '.avi'] },
    maxSize: MAX_SIZE,
    maxFiles: 1,
    disabled,
  });

  return (
    <motion.div
      {...getRootProps()}
      className={`upload-zone ${isDragActive ? 'drag-active' : ''} ${disabled ? 'disabled' : ''}`}
      whileHover={!disabled ? { scale: 1.01 } : {}}
      whileTap={!disabled ? { scale: 0.99 } : {}}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <input {...getInputProps()} />
      <div className="upload-zone__icon">
        {isDragActive ? '🌿' : '🎬'}
      </div>
      <div className="upload-zone__text">
        {isDragActive ? (
          <p className="upload-zone__primary">Release to begin the magic...</p>
        ) : (
          <>
            <p className="upload-zone__primary">Drop your video here</p>
            <p className="upload-zone__secondary">
              or <span className="upload-zone__link">browse files</span>
            </p>
            <p className="upload-zone__hint">MP4, MOV, WEBM · max 100MB · up to 15s</p>
          </>
        )}
      </div>
    </motion.div>
  );
}
