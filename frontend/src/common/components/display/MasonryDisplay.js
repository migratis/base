import Badge from 'react-bootstrap/Badge';
import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
} from 'react-icons/io5';

const MasonryDisplay = ({
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
  const relationshipsConfig = config?.relationships || {};

  const tval = (key, fallback) => t ? t(key, fallback) : fallback || key;

  const getFieldLabel = (fieldName) => {
    return fieldsConfig[fieldName]?.label || fieldName;
  };

  const displayFields = entity.fields
    .slice(0, config?.display_mode_options?.max_fields || 3);

  const getDisplayValue = (field, value) => {
    if (value === null || value === undefined) return null;
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
    if (field.field_type === 'text') {
      const truncated = String(value).substring(0, 150);
      return truncated.length < String(value).length ? `${truncated}...` : truncated;
    }

    const fieldConfig = fieldsConfig[field.name];
    const options = fieldConfig?.options;
    if (options && Array.isArray(options)) {
      const option = options.find(o => o.value === value);
      if (option) return option.label || option.value;
    }

    if (typeof value === 'object' && value !== null) {
      if (value.label) return String(value.label);
      if (value.value !== undefined) return String(value.value);
      return JSON.stringify(value);
    }

    return String(value);
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
    return getDisplayValue(field, value) || '—';
  };

  const getPrimaryField = () => {
    return displayFields.find((f) => f.name === 'name' || f.name === 'title') || displayFields[0];
  };

  const primaryField = getPrimaryField();

  const resolveRelLabel = (fieldName, value) => {
    if (!value) return [];
    const opts = relOptions[fieldName] || [];
    if (Array.isArray(value)) {
      return value.map((id) => {
        const opt = opts.find((o) => o.value === id);
        return opt ? opt.label : `#${id}`;
      });
    }
    const opt = opts.find((o) => o.value === value);
    return opt ? [opt.label] : [`#${value}`];
  };

  return (
    <div className="migratis-masonry" style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '1rem',
    }}>
      {records.map((record) => (
        <div
          key={record.id}
          style={{
            background: '#fff',
            border: '1px solid #dee2e6',
            borderRadius: '0.25rem',
            minWidth: '240px',
            maxWidth: '320px',
            flex: '1 1 240px',
            position: 'relative',
          }}
        >
          <div className="p-2">
            {primaryField && (
              <div style={{ fontWeight: 'bold', fontSize: '1.1em', marginBottom: '0.5rem' }}>
                {renderValue(primaryField, record.data[primaryField.name]) || tval('unnamed-record', 'Unnamed')}
              </div>
            )}
            {displayFields.filter((f) => f !== primaryField).map((field) => (
              <div key={field.name} className="mb-1">
                <small className="text-muted">{getFieldLabel(field.name)}: </small>
                <span style={{ fontSize: '0.9em' }}>
                  {renderValue(field, record.data[field.name])}
                </span>
              </div>
            ))}
            {(entity.relationships || []).filter((r) => record.data[r.field_name]).slice(0, 2).map((rel) => {
              const labels = resolveRelLabel(rel.field_name, record.data[rel.field_name]);
              if (!labels || labels.length === 0) return null;
              const relLabel = relationshipsConfig[rel.field_name]?.label || rel.related_entity;
              return (
                <div key={rel.field_name} className="mt-2">
                  <small className="text-muted">{relLabel}: </small>
                  <div className="d-flex flex-wrap gap-1 mt-1">
                    {labels.slice(0, 3).map((label, i) => (
                      <Badge key={i} bg="info" style={{ fontSize: '0.75em' }}>
                        {label}
                      </Badge>
                    ))}
                    {labels.length > 3 && (
                      <Badge bg="secondary" style={{ fontSize: '0.75em' }}>
                        +{labels.length - 3}
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="d-flex justify-content-end gap-2 p-2" style={{ position: 'absolute', bottom: 0, right: 0 }}>
            {onEdit && (
              <span className="link action" onClick={() => onEdit(record)}>
                <EditIcon />
              </span>
            )}
            {onDelete && (
              <span className="link action" onClick={() => onDelete(record.id)}>
                <TrashIcon />
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MasonryDisplay;
