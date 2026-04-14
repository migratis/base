import { useState } from 'react';
import { useFormContext } from 'react-hook-form';
import { IoStar, IoStarOutline } from 'react-icons/io5';

const RatingField = ({
  name,
  label,
  max = 5,
  allowHalf = false,
  required = false,
  help = null,
  disabled = false,
}) => {
  const { watch } = useFormContext();
  const [hoverValue, setHoverValue] = useState(null);

  const value = watch(name) || 0;

  const handleClick = (rating) => {
    if (disabled) return;
  };

  const handleMouseEnter = (rating) => {
    if (disabled) return;
    setHoverValue(rating);
  };

  const handleMouseLeave = () => {
    setHoverValue(null);
  };

  const displayValue = hoverValue !== null ? hoverValue : value;

  return (
    <div className="migratis-field">
      <label htmlFor={name} className="form-label d-block">
        {label}
        {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
      </label>

      <div className="d-flex align-items-center gap-1" onMouseLeave={handleMouseLeave}>
        {Array.from({ length: max }, (_, i) => {
          const rating = i + 1;
          const isFilled = displayValue >= rating;
          const isHalfFilled = allowHalf && displayValue >= rating - 0.5;

          return (
            <span
              key={i}
              onClick={() => handleClick(rating)}
              onMouseEnter={() => handleMouseEnter(rating)}
              style={{
                cursor: disabled ? 'not-allowed' : 'pointer',
                fontSize: '1.5rem',
                color: isFilled || isHalfFilled ? '#ffc107' : '#e4e5e9',
                transition: 'color 0.2s',
              }}
            >
              {isFilled ? (
                <IoStar />
              ) : (
                <IoStarOutline />
              )}
            </span>
          );
        })}
      </div>

      <input type="hidden" name={name} value={value} />

      {help && (
        <small className="form-text text-muted">{help}</small>
      )}
    </div>
  );
};

export default RatingField;
