import { motion } from 'framer-motion';

export default function ProgressBar({ phase, uploadProgress, jobStatus }) {
  const isUploading = phase === 'uploading';
  const isProcessing = phase === 'processing';

  const progressValue = isUploading
    ? uploadProgress
    : jobStatus?.progress ?? 0;

  const message = isUploading
    ? `Uploading your video... ${uploadProgress}%`
    : (jobStatus?.current_step || 'Warming up the paintbrushes...');

  return (
    <div className="progress-wrap">
      <div className="progress-bar__track">
        <motion.div
          className="progress-bar__fill"
          initial={{ width: '0%' }}
          animate={{ width: `${progressValue}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>

      <div className="progress-bar__info">
        <motion.p
          key={message}
          className="progress-bar__message"
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
          transition={{ duration: 0.3 }}
        >
          🎨 {message}
        </motion.p>

        {isProcessing && jobStatus?.frames_total > 0 && (
          <p className="progress-bar__frames">
            Frame {jobStatus.frames_done} / {jobStatus.frames_total}
          </p>
        )}
      </div>
    </div>
  );
}
