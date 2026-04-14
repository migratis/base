import { Form } from 'react-bootstrap';
import { useFormContext } from 'react-hook-form';

const ToggleField = ({
  name,
  label,
  required = false,
  help = null,
  disabled = false,
}) => {
  const { register } = useFormContext();

  return (
    <div className="migratis-field">
      <Form.Check
        type="switch"
        id={name}
        label={
          <>
            {label}
            {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
          </>
        }
        {...register(name)}
        disabled={disabled}
        className="fs-6"
      />

      {help && (
        <small className="form-text text-muted">{help}</small>
      )}
    </div>
  );
};

export default ToggleField;
