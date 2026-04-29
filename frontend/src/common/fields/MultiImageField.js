import { useState, useEffect, useRef } from 'react';
import { useFormContext } from 'react-hook-form';
import { Form, Image } from 'react-bootstrap';

const MultiImageField = ({
  name,
  label,
  required = false,
  help = null,
  disabled = false,
  accept = 'image/*',
  maxImages = 6,
}) => {
  const { watch, setValue } = useFormContext();
  const inputRef = useRef(null);
  const [previews, setPreviews] = useState([]);

  const value = watch(name);

  useEffect(() => {
    if (!value) { setPreviews([]); return; }
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) { setPreviews(parsed); return; }
    } catch {}
    // Legacy single base64 string from ImageField
    if (typeof value === 'string' && value.startsWith('data:')) {
      setPreviews([value]);
    }
  }, [value]);

  const handleAdd = (e) => {
    const files = Array.from(e.target.files).slice(0, maxImages - previews.length);
    if (!files.length) return;
    Promise.all(files.map(file => new Promise(resolve => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(file);
    }))).then(newBase64s => {
      const updated = [...previews, ...newBase64s];
      setPreviews(updated);
      setValue(name, JSON.stringify(updated));
    });
    e.target.value = '';
  };

  const handleRemove = (idx) => {
    const updated = previews.filter((_, i) => i !== idx);
    setPreviews(updated);
    setValue(name, updated.length ? JSON.stringify(updated) : '');
  };

  const canAdd = !disabled && previews.length < maxImages;

  return (
    <div className="migratis-field">
      <label className="form-label">
        {label}
        {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
        <span className="text-muted ms-2" style={{ fontSize: '12px', fontWeight: 'normal' }}>
          {previews.length}/{maxImages}
        </span>
      </label>

      {previews.length > 0 && (
        <div className="d-flex flex-wrap gap-2 mb-2">
          {previews.map((src, idx) => (
            <div key={idx} style={{ position: 'relative', display: 'inline-block' }}>
              <Image
                src={src}
                thumbnail
                style={{ width: '80px', height: '80px', objectFit: 'cover' }}
              />
              {!disabled && (
                <button
                  type="button"
                  onClick={() => handleRemove(idx)}
                  style={{
                    position: 'absolute', top: '-6px', right: '-6px',
                    width: '18px', height: '18px', borderRadius: '50%',
                    background: '#dc3545', color: '#fff', border: 'none',
                    fontSize: '11px', lineHeight: 1, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                >×</button>
              )}
            </div>
          ))}
        </div>
      )}

      {canAdd && (
        <Form.Control
          ref={inputRef}
          type="file"
          accept={accept}
          multiple
          onChange={handleAdd}
          disabled={disabled}
          className="mb-1"
          style={{ maxWidth: '320px' }}
        />
      )}

      {canAdd && previews.length > 0 && (
        <small className="text-muted d-block mb-1">
          {maxImages - previews.length} slot{maxImages - previews.length !== 1 ? 's' : ''} remaining
        </small>
      )}

      {help && <small className="form-text text-muted">{help}</small>}
    </div>
  );
};

export default MultiImageField;
