import { useState } from 'react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

export default function VideoTrimmer({ duration, onChange }) {
  const max = Math.floor(duration);
  const [range, setRange] = useState([0, Math.min(15, max)]);

  const handleChange = (val) => {
    const [start, end] = val;
    // Enforce max 15s window
    if (end - start > 15) {
      const adjusted = [start, start + 15];
      setRange(adjusted);
      onChange(adjusted[0], adjusted[1]);
    } else {
      setRange(val);
      onChange(val[0], val[1]);
    }
  };

  const fmt = (s) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  };

  return (
    <div className="trimmer">
      <div className="trimmer__header">
        <span className="trimmer__label">✂️ Select 15s segment</span>
        <span className="trimmer__range">
          {fmt(range[0])} → {fmt(range[1])}
          <em> ({(range[1] - range[0]).toFixed(1)}s)</em>
        </span>
      </div>
      <Slider
        range
        min={0}
        max={max}
        step={0.1}
        value={range}
        onChange={handleChange}
        trackStyle={[{ background: 'var(--accent)' }]}
        handleStyle={[
          { borderColor: 'var(--accent)', background: 'var(--surface)' },
          { borderColor: 'var(--accent)', background: 'var(--surface)' },
        ]}
        railStyle={{ background: 'var(--border)' }}
      />
      <p className="trimmer__hint">
        Video is {fmt(duration)} long — trim to a 15s window to continue.
      </p>
    </div>
  );
}
