import { motion } from 'framer-motion';
import { getDownloadUrl } from '../api/client';

export default function DownloadButton({ jobId }) {
  return (
    <motion.a
      href={getDownloadUrl(jobId)}
      download="ghiblilens_output.mp4"
      className="btn btn--download"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.97 }}
    >
      ⬇️ Download your Ghibli video
    </motion.a>
  );
}
