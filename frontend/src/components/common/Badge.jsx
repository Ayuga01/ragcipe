import { X } from 'lucide-react';
import './Badge.css';

export default function Badge({
  children,
  variant = 'default',
  onClose,
  className = '',
  style = {},
}) {
  return (
    <span
      className={`badge badge--${variant} ${className}`}
      style={style}
    >
      {children}
      {onClose && (
        <button className="badge__close" onClick={onClose} aria-label="Remove">
          <X size={10} />
        </button>
      )}
    </span>
  );
}
