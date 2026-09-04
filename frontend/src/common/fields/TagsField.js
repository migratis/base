import { useEffect, useState } from 'react';
import { useFormContext } from 'react-hook-form';
import { Form, InputGroup, Badge } from 'react-bootstrap';
import { IoClose } from 'react-icons/io5';

/**
 * Whatever the column holds, as a list of tags.
 *
 * `render_as: 'tags'` is a display choice over an ordinary `string` field, so
 * nothing guarantees the stored value is a list: an external lookup fills it
 * with a comma-joined string (OMDb's `"Genre": "Action, Adventure, Sci-Fi"`,
 * and the mapper joins a `[]` path with `, ` by design), and so do a seeded
 * row, an agent write, and every row that predates someone switching this
 * field from `input` to `tags`. A reader that assumes the list crashes the
 * whole form on all four.
 *
 * A string is split on commas because that is the shape every one of those
 * producers writes. Anything with no honest reading — a number, an object —
 * is no tags at all rather than a fabricated one; the user adds their own.
 */
const toTags = (value) => {
  if (Array.isArray(value)) return value;
  if (typeof value !== 'string') return [];
  return value.split(',').map((tag) => tag.trim()).filter(Boolean);
};

const TagsField = ({
  name,
  label,
  suggestions = [],
  placeholder = 'Type and press Enter',
  required = false,
  help = null,
  disabled = false,
}) => {
  const { watch, setValue } = useFormContext();
  const [inputValue, setInputValue] = useState('');

  const raw = watch(name);
  const value = toTags(raw);

  // The render is only half of it. Showing the string as tags while the form
  // still submits the string would leave one column holding two shapes — prod
  // app 6's `"197.8"` in a decimal, in a different column type. Normalise the
  // value the form actually carries, once, as soon as it is seen.
  useEffect(() => {
    if (raw !== undefined && !Array.isArray(raw)) {
      setValue(name, toTags(raw), { shouldDirty: false });
    }
  }, [raw, name, setValue]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      const newTag = inputValue.trim();
      if (!value.includes(newTag)) {
        setValue(name, [...value, newTag]);
      }
      setInputValue('');
    } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
      setValue(name, value.slice(0, -1));
    }
  };

  const handleRemove = (tagToRemove) => {
    setValue(name, value.filter(tag => tag !== tagToRemove));
  };

  const handleSuggestionClick = (suggestion) => {
    if (!value.includes(suggestion)) {
      setValue(name, [...value, suggestion]);
    }
  };

  return (
    <div className="migratis-field">
      <label htmlFor={name} className="form-label">
        {label}
        {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
      </label>

      <InputGroup>
        <Form.Control
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
        />
      </InputGroup>

      <input type="hidden" name={name} value={JSON.stringify(value)} />

      {value.length > 0 && (
        <div className="d-flex flex-wrap gap-1 mt-2">
          {value.map((tag, index) => (
            <Badge
              key={index}
              bg="primary"
              className="d-flex align-items-center gap-1 px-2 py-1"
              style={{ fontSize: '0.875rem' }}
            >
              {tag}
              {!disabled && (
                <span
                  onClick={() => handleRemove(tag)}
                  style={{ cursor: 'pointer' }}
                >
                  <IoClose size={14} />
                </span>
              )}
            </Badge>
          ))}
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="d-flex flex-wrap gap-1 mt-2">
          {suggestions
            .filter(s => !value.includes(s))
            .map((suggestion, index) => (
              <Badge
                key={index}
                bg="light"
                text="dark"
                className="px-2 py-1"
                style={{ cursor: 'pointer', border: '1px solid #dee2e6' }}
                onClick={() => handleSuggestionClick(suggestion)}
              >
                + {suggestion}
              </Badge>
            ))}
        </div>
      )}

      {help && (
        <small className="form-text text-muted">{help}</small>
      )}
    </div>
  );
};

export default TagsField;
