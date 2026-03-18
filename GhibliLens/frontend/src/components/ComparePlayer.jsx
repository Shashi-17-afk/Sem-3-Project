import { useState } from 'react';
import ReactPlayer from 'react-player';

export default function ComparePlayer({ originalUrl, ghibliUrl }) {
  const [view, setView] = useState('ghibli'); // 'original' | 'ghibli' | 'split'

  return (
    <div className="compare">
      <div className="compare__tabs">
        {['original', 'ghibli', 'split'].map((v) => (
          <button
            key={v}
            className={`compare__tab ${view === v ? 'active' : ''}`}
            onClick={() => setView(v)}
          >
            {v === 'original' ? '🎥 Original' : v === 'ghibli' ? '🌿 Ghibli' : '↔ Compare'}
          </button>
        ))}
      </div>

      <div className={`compare__players ${view === 'split' ? 'split' : 'single'}`}>
        {(view === 'original' || view === 'split') && (
          <div className="compare__player-wrap">
            <p className="compare__label">Original</p>
            <ReactPlayer
              url={originalUrl}
              controls
              playing={false}
              width="100%"
              height="100%"
            />
          </div>
        )}
        {(view === 'ghibli' || view === 'split') && (
          <div className="compare__player-wrap">
            <p className="compare__label">✨ Ghibli</p>
            <ReactPlayer
              url={ghibliUrl}
              controls
              playing={false}
              width="100%"
              height="100%"
            />
          </div>
        )}
      </div>
    </div>
  );
}
