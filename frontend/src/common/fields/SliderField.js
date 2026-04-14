import { Form } from 'react-bootstrap';
import { useFormContext, Controller } from 'react-hook-form';

const SliderField = ({
  name,
  label,
  min = 0,
  max = 100,
  step = 1,
  required = false,
  help = null,
  disabled = false,
}) => {
  const { control } = useFormContext();

  return (
    <div className="migratis-field">
      <label htmlFor={name} className="form-label">
        {label}
        {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
      </label>

      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <div className="d-flex align-items-center gap-2">
            <Form.Range
              id={name}
              min={min}
              max={max}
              step={step}
              value={field.value ?? min}
              onChange={(e) => field.onChange(parseFloat(e.target.value))}
              disabled={disabled}
              className="flex-grow-1"
            />
            <span className="badge bg-secondary" style={{ minWidth: '50px', textAlign: 'center' }}>
              {field.value ?? min}
            </span>
          </div>
        )}
      />

      <div className="d-flex justify-content-between small text-muted">
        <span>{min}</span>
        <span>{max}</span>
      </div>

      {help && (
        <small className="form-text text-muted">{help}</small>
      )}
    </div>
  );
};

export default SliderField;
