import { useState, useEffect } from 'react';
import { useFormContext } from 'react-hook-form';
import { Form, Image } from 'react-bootstrap';

const ImageField = ({
  name,
  label,
  required = false,
  help = null,
  disabled = false,
  accept = 'image/*',
}) => {
  const { watch, setValue } = useFormContext();
  const [preview, setPreview] = useState(null);

  const value = watch(name);

  useEffect(() => {
    if (value && value.startsWith('data:') && !preview) {
      setPreview(value);
    }
  }, [value, preview]);

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
        setValue(name, reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="migratis-field">
      <label htmlFor={name} className="form-label">
        {label}
        {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
      </label>

      <Form.Control
        type="file"
        id={name}
        name={name}
        accept={accept}
        onChange={handleChange}
        disabled={disabled}
        className="mb-2"
      />

      {(preview || value) && (
        <div className="mb-2">
          <Image
            src={preview || value}
            thumbnail
            style={{ maxWidth: '200px', maxHeight: '200px' }}
          />
        </div>
      )}

      <input type="hidden" name={name} value={value || ''} />

      {help && (
        <small className="form-text text-muted">{help}</small>
      )}
    </div>
  );
};

export default ImageField;
