import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
} from 'react-icons/io5';

const ListDisplay = ({
  entity,
  records,
  relOptions = {},
  config = {},
  onEdit,
  onDelete,
  t,
}) => {
  if (!records || records.length === 0) {
    return null;
  }

  const fieldsConfig = config?.fields || {};

  const tval = (key, fallback) => t ? t(key, fallback) : fallback || key;

  const getFieldLabel = (fieldName) => {
    return fieldsConfig[fieldName]?.label || fieldName;
  };

  const getPrimaryField = () => {
    return entity.fields.find((f) =>
      f.name === 'name' || f.name === 'title'
    ) || entity.fields[0];
  };

  const primaryField = getPrimaryField();

  const getSecondaryFields = () => {
    return entity.fields
      .filter((f) => f !== primaryField)
      .slice(0, config?.display_mode_options?.max_fields || 2);
  };

  const secondaryFields = getSecondaryFields();

  const formatValue = (field, value) => {
    if (value === null || value === undefined) return '—';
    // Handle {label, value} objects from select fields
    if (typeof value === 'object' && value !== null) {
      return value.label || value.value || '—';
    }
    if (field.field_type === 'boolean') {
      return value ? tval('true', 'Yes') : tval('false', 'No');
    }
    if (field.field_type === 'date' || field.field_type === 'datetime') {
      const renderAs = fieldsConfig?.[field.name]?.render_as;
      if (renderAs === 'time') return String(value).slice(11, 16);
      if (renderAs === 'datetime') {
        const d = new Date(value);
        return isNaN(d) ? String(value) : d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      const d = new Date(value);
      return isNaN(d) ? String(value).slice(0, 10) : d.toLocaleDateString();
    }
    const truncated = String(value);
    return truncated.length > 40 ? `${truncated.substring(0, 40)}...` : truncated;
  };

  const _isHexColor = (v) => typeof v === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(v.trim());

  const renderValue = (field, value) => {
    const renderAs = fieldsConfig?.[field.name]?.render_as;
    const raw = value != null ? String(value).trim() : '';
    if (renderAs === 'color' || _isHexColor(raw)) {
      return (
        <span className="d-inline-flex align-items-center gap-1">
          <span style={{ display: 'inline-block', width: 14, height: 14, borderRadius: 2, background: raw, border: '1px solid rgba(0,0,0,0.2)', flexShrink: 0 }} />
          {raw}
        </span>
      );
    }
    return formatValue(field, value);
  };

  return (
    <div className="list-display">
      {records.map((record) => (
        <div
          key={record.id}
          className="d-flex align-items-center border-bottom py-2 px-1"
          style={{ minHeight: '48px' }}
        >
          <div className="flex-grow-1 me-3" style={{ overflow: 'hidden' }}>
            <div style={{ fontWeight: '500', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {primaryField ? renderValue(primaryField, record.data[primaryField.name]) : tval('unnamed-record', 'Unnamed')}
            </div>
            {secondaryFields.length > 0 && (
              <small className="text-muted" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {secondaryFields.map((f, i) => (
                  <span key={f.name}>
                    {i > 0 && ' • '}
                    <span>{getFieldLabel(f.name)}: </span>
                    {renderValue(f, record.data[f.name])}
                  </span>
                ))}
              </small>
            )}
          </div>
          <div className="d-flex gap-2">
            <span className="link action" onClick={() => onEdit(record)}>
              <EditIcon />
            </span>
            <span className="link action" onClick={() => onDelete(record.id)}>
              <TrashIcon />
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ListDisplay;
