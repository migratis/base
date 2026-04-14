import { useFormContext } from 'react-hook-form';
import { Form, InputGroup } from 'react-bootstrap';

const CurrencyField = ({
  name,
  label,
  currency = 'USD',
  symbol = '$',
  min = 0,
  max = 999999,
  step = 0.01,
  required = false,
  help = null,
  disabled = false,
  placeholder = '0.00',
}) => {
  const { register } = useFormContext();

  return (
    <div className="migratis-field">
      <label htmlFor={name} className="form-label">
        {label}
        {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
      </label>

      <InputGroup>
        <InputGroup.Text>{symbol}</InputGroup.Text>
        <Form.Control
          type="number"
          id={name}
          min={min}
          max={max}
          step={step}
          placeholder={placeholder}
          disabled={disabled}
          {...register(name, { valueAsNumber: true })}
        />
      </InputGroup>

      <input type="hidden" name={`${name}_currency`} value={currency} />

      {help && (
        <small className="form-text text-muted">{help}</small>
      )}
    </div>
  );
};

export default CurrencyField;
