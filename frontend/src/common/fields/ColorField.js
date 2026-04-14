import { Form, InputGroup } from 'react-bootstrap';
import { useFormContext, useController } from 'react-hook-form';

const ColorField = ({
  name,
  label,
  required = false,
  help = null,
  disabled = false,
}) => {
  const { control } = useFormContext();
  const { field } = useController({ name, control, defaultValue: '#000000' });

  const value = field.value || '#000000';

  return (
    <div className="migratis-field">
      <label htmlFor={name} className="form-label">
        {label}
        {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
      </label>

      <InputGroup>
        <InputGroup.Text>
          <div
            style={{
              width: '24px',
              height: '24px',
              backgroundColor: value,
              border: '1px solid #dee2e6',
              borderRadius: '4px',
            }}
          />
        </InputGroup.Text>
        <Form.Control
          type="color"
          id={name}
          value={value}
          onChange={(e) => field.onChange(e.target.value)}
          onBlur={field.onBlur}
          disabled={disabled}
          style={{ maxWidth: '100px' }}
        />
        <Form.Control
          type="text"
          value={value}
          onChange={(e) => field.onChange(e.target.value)}
          onBlur={field.onBlur}
          disabled={disabled}
          placeholder="#000000"
        />
      </InputGroup>

      {help && (
        <small className="form-text text-muted">{help}</small>
      )}
    </div>
  );
};

export default ColorField;
