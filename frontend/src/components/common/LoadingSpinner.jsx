import './LoadingSpinner.css';

const sizes = {
  sm: 24,
  md: 40,
  lg: 56,
};

export default function LoadingSpinner({ size = 'md', text = '' }) {
  const s = sizes[size] || sizes.md;
  const strokeWidth = size === 'sm' ? 3 : 2.5;
  const radius = (s - strokeWidth * 2) / 2;
  const circumference = radius * 2 * Math.PI;

  return (
    <div className="loading-spinner">
      <div className="loading-spinner__glow" style={{ width: s, height: s }}>
        <svg
          className="loading-spinner__svg"
          width={s}
          height={s}
          viewBox={`0 0 ${s} ${s}`}
        >
          {/* Track */}
          <circle
            className="loading-spinner__track"
            cx={s / 2}
            cy={s / 2}
            r={radius}
            fill="none"
            strokeWidth={strokeWidth}
          />
          {/* Spinner */}
          <circle
            className="loading-spinner__circle"
            cx={s / 2}
            cy={s / 2}
            r={radius}
            fill="none"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={circumference * 0.7}
            strokeLinecap="round"
          />
        </svg>
      </div>
      {text && <p className="loading-spinner__text">{text}</p>}
    </div>
  );
}
