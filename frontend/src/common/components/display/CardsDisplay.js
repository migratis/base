import { useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Image from 'react-bootstrap/Image';
import Modal from 'react-bootstrap/Modal';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
  IoCardOutline as CardIcon,
  IoInformationCircleOutline as InfoIcon,
  IoImageOutline as ImagePlaceholderIcon,
} from 'react-icons/io5';

const CardsDisplay = ({
  entity,
  records,
  relOptions = {},
  config = {},
  onEdit,
  onDelete,
  t,
}) => {
  const [expandedRecord, setExpandedRecord] = useState(null);

  if (!records || records.length === 0) {
    return null;
  }

  const fieldsConfig = config?.fields || {};
  const relationshipsConfig = config?.relationships || {};
  const displayOptions = config?.display_mode_options || {};

  const tval = (key, fallback) => t ? t(key, fallback) : fallback || key;

  const thumbnailFieldName = displayOptions?.thumbnail_field;

  const getFieldLabel = (fieldName) => {
    return fieldsConfig[fieldName]?.label || fieldName;
  };

  const getThumbnailUrl = (record) => {
    if (!thumbnailFieldName) return null;
    const value = record.data[thumbnailFieldName];
    if (!value || typeof value !== 'string') return null;
    if (value.startsWith('data:') || value.startsWith('http') || value.startsWith('/')) {
      return value;
    }
    return null;
  };

  const imageFieldNames = new Set(
    entity.fields
      .filter(f => f.field_type === 'file' || fieldsConfig[f.name]?.render_as === 'image')
      .map(f => f.name)
  );
  if (thumbnailFieldName) imageFieldNames.add(thumbnailFieldName);

  const displayFields = entity.fields
    .filter((f) => !imageFieldNames.has(f.name));

  const getDisplayValue = (field, value) => {
    if (value === null || value === undefined) return null;
    if (field.field_type === 'boolean') {
      return value ? tval('true', 'Yes') : tval('false', 'No');
    }

    const fieldConfig = fieldsConfig[field.name];
    const options = fieldConfig?.options;
    if (options && Array.isArray(options)) {
      const option = options.find(o => o.value === value);
      if (option) return option.label || option.value;
    }

    if (field.field_type === 'date' || field.field_type === 'datetime') {
      const renderAs = fieldConfig?.render_as;
      if (renderAs === 'time') return String(value).slice(11, 16);
      if (renderAs === 'datetime') {
        const d = new Date(value);
        return isNaN(d) ? String(value) : d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      const d = new Date(value);
      return isNaN(d) ? String(value).slice(0, 10) : d.toLocaleDateString();
    }

    if (typeof value === 'object') {
      if (value.label) return value.label;
      if (value.value !== undefined) return value.value;
      return JSON.stringify(value);
    }

    return String(value);
  };

  const _isHexColor = (v) => typeof v === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(v.trim());

  const renderValue = (field, value) => {
    const renderAs = fieldsConfig[field.name]?.render_as;
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

  const _PRIMARY_NAMES = ['name', 'label', 'title', 'code', 'reference', 'ref', 'number', 'slug'];
  const displayLabelFields = displayOptions?.display_label_fields || config?.display_label_fields || [];
  const isPrimaryField = (fieldName) => {
    if (displayLabelFields.includes(fieldName)) return true;
    const lower = fieldName?.toLowerCase() || '';
    return _PRIMARY_NAMES.some((p) => lower === p || lower.endsWith('_' + p));
  };

  const getPrimaryField = () => {
    return displayFields.find((f) => isPrimaryField(f.name)) || displayFields[0];
  };

  const primaryField = getPrimaryField();

  const resolveRelLabel = (fieldName, value) => {
    if (!value) return null;
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
    <div className="d-flex flex-wrap gap-3">
      {records.map((record) => {
        const thumbnailUrl = getThumbnailUrl(record);

        return (
          <div key={record.id} className="card shadow-sm" style={{ minWidth: '280px', maxWidth: '350px', flex: '1 1 280px' }}>
            <div
              style={{ height: '150px', overflow: 'hidden', background: '#f0f0f0', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              onClick={() => setExpandedRecord(record)}
            >
              {thumbnailUrl ? (
                <Image
                  src={thumbnailUrl}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              ) : (
                <ImagePlaceholderIcon style={{ fontSize: '3rem', color: '#ccc' }} />
              )}
            </div>
            <div className="card-body">
              {primaryField && (
                <h6 className="card-title text-truncate mb-2" title={getDisplayValue(primaryField, record.data[primaryField.name]) || tval('unnamed-record', 'Unnamed')}>
                  {getDisplayValue(primaryField, record.data[primaryField.name]) || tval('unnamed-record', 'Unnamed')}
                </h6>
              )}
              {displayFields.filter((f) => f !== primaryField).slice(0, 3).map((field) => {
                const value = record.data[field.name];
                const isDescription = field.name.toLowerCase() === 'description';

                if (isDescription && value) {
                  return (
                    <div key={field.name} className="mb-1 small d-flex align-items-center gap-1">
                      <span className="text-muted">{getFieldLabel(field.name)}: </span>
                      <OverlayTrigger
                        trigger={['hover', 'focus']}
                        placement="top"
                        overlay={
                          <Popover id={`popover-card-${record.id}-${field.name}`}>
                            <Popover.Body>{value}</Popover.Body>
                          </Popover>
                        }
                      >
                        <span className="popover-trigger"><InfoIcon /></span>
                      </OverlayTrigger>
                    </div>
                  );
                }

                return (
                  <div key={field.name} className="mb-1 small">
                    <span className="text-muted">{getFieldLabel(field.name)}: </span>
                    <span className="text-truncate d-inline-block" style={{ maxWidth: '200px', verticalAlign: 'bottom' }}>
                      {renderValue(field, value)}
                    </span>
                  </div>
                );
              })}
              {(entity.relationships || []).filter((rel) => record.data[rel.field_name]).map((rel) => {
                const labels = resolveRelLabel(rel.field_name, record.data[rel.field_name]);
                if (!labels || labels.length === 0) return null;
                const relLabel = relationshipsConfig[rel.field_name]?.label || rel.field_name;
                return (
                  <div key={rel.field_name} className="mb-1 small">
                    <span className="text-muted">{relLabel}: </span>
                    <div className="d-inline">
                      {labels.slice(0, 3).map((label, i) => (
                        <Badge key={i} bg="secondary" className="me-1">
                          {label}
                        </Badge>
                      ))}
                      {labels.length > 3 && (
                        <Badge bg="light" text="dark">+{labels.length - 3}</Badge>
                      )}
                    </div>
                  </div>
                );
              })}
              {(onEdit || onDelete) && (
                <div className="d-flex gap-2 mt-2 pt-2 border-top">
                  <span className="ms-auto"></span>
                  {onEdit && (
                    <span className="link action" onClick={() => onEdit(record)} title={tval('edit', 'Edit')}>
                      <EditIcon />
                    </span>
                  )}
                  {onDelete && (
                    <span className="link action text-danger" onClick={() => onDelete(record.id)} title={tval('delete', 'Delete')}>
                      <TrashIcon />
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}

      <Modal show={!!expandedRecord} onHide={() => setExpandedRecord(null)} size="lg" className="migratis-modal">
        <Modal.Header className="migratis-modal-header">
          <span className="migratis-modal-icon"><CardIcon /></span>
          <Modal.Title className="migratis-modal-title">
            {expandedRecord && primaryField
              ? expandedRecord.data[primaryField.name] || tval('unnamed-record', 'Unnamed')
              : ''}
          </Modal.Title>
          <button className="migratis-modal-close" onClick={() => setExpandedRecord(null)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 512 512"><path fill="currentColor" d="M400 145.7L366.3 112L256 222.7L145.7 112L112 145.7l110.3 110.3L112 366.3l33.7 33.7L256 333.3l110.3 110.3L400 366.3L289.7 256z"/></svg>
          </button>
        </Modal.Header>
        <Modal.Body className="text-center">
          {expandedRecord && getThumbnailUrl(expandedRecord) && (
            <img
              src={getThumbnailUrl(expandedRecord)}
              alt={primaryField ? expandedRecord.data[primaryField.name] : ''}
              style={{ maxWidth: '100%', maxHeight: '50vh', objectFit: 'contain' }}
            />
          )}
          {expandedRecord && (
            <div className="text-start mt-3">
              {entity.fields.filter(f => f !== primaryField && !imageFieldNames.has(f.name)).map((field) => (
                <div key={field.name} className="mb-2">
                  <strong>{getFieldLabel(field.name)}:</strong>
                  <div>{renderValue(field, expandedRecord.data[field.name])}</div>
                </div>
              ))}
              {(entity.relationships || []).map((rel) => {
                const labels = resolveRelLabel(rel.field_name, expandedRecord.data[rel.field_name]);
                if (!labels || labels.length === 0) return null;
                const relLabel = relationshipsConfig[rel.field_name]?.label || rel.field_name;
                return (
                  <div key={rel.field_name} className="mb-2">
                    <strong>{relLabel}:</strong>
                    <div>
                      {labels.map((label, i) => (
                        <Badge key={i} bg="secondary" className="me-1">
                          {label}
                        </Badge>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          {onEdit && expandedRecord && (
            <Button variant="primary" onClick={() => { onEdit(expandedRecord); setExpandedRecord(null); }}>
              <EditIcon /> {tval('edit', 'Edit')}
            </Button>
          )}
          <Button variant="secondary" onClick={() => setExpandedRecord(null)}>
            {tval('close', 'Close')}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default CardsDisplay;
