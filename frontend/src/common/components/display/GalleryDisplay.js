import { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
  IoImageOutline as ImageIcon,
  IoInformationCircleOutline as InfoIcon,
} from 'react-icons/io5';
import InteractionRowActions from '../InteractionRowActions';

const GalleryDisplay = ({
  entity,
  records,
  relOptions = {},
  config = {},
  onEdit,
  onDelete,
  onInteraction,
  viewAs,
  getRoleRank,
  t,
}) => {
  const [expandedRecord, setExpandedRecord] = useState(null);

  if (!records || records.length === 0) {
    return null;
  }

  const fieldsConfig = config?.fields || {};
  const displayOptions = config?.display_mode_options || {};

  const tval = (key, fallback) => t ? t(key, fallback) : fallback || key;

  const thumbnailFieldName = displayOptions?.thumbnail_field;

  const getThumbnailSrc = (record) => {
    if (!thumbnailFieldName) return null;
    const value = record.data[thumbnailFieldName];
    if (!value) return null;
    // Multi-image: JSON array — use first entry
    if (typeof value === 'string' && value.startsWith('[')) {
      try { const arr = JSON.parse(value); if (arr?.[0]) return arr[0]; } catch {}
    }
    if (typeof value !== 'string' || !value.startsWith('data:')) return null;
    return value;
  };

  const getFieldLabel = (fieldName) => {
    return fieldsConfig[fieldName]?.label || fieldName;
  };

  const getPrimaryField = () => {
    return entity.fields.find((f) =>
      f.name === 'name' || f.name === 'title'
    );
  };

  const primaryField = getPrimaryField();

  const imageFieldNames = new Set(
    entity.fields
      .filter(f => f.field_type === 'file' || fieldsConfig[f.name]?.render_as === 'image')
      .map(f => f.name)
  );
  imageFieldNames.add(thumbnailFieldName);

  const getDisplayFields = () => {
    return entity.fields
      .filter((f) =>
        f !== primaryField &&
        fieldsConfig[f.name] &&
        !imageFieldNames.has(f.name)
      )
      .slice(0, config?.display_mode_options?.max_fields || 3);
  };

  const displayFields = getDisplayFields();

  const formatValue = (field, value) => {
    if (value === null || value === undefined) return '—';
    if (field.field_type === 'boolean') {
      return value ? tval('true', 'Yes') : tval('false', 'No');
    }

    const fieldConfig = fieldsConfig[field.name];
    const options = fieldConfig?.options;
    if (options && Array.isArray(options)) {
      const option = options.find(o => o.value === value);
      if (option) return option.label || option.value;
    }

    if (typeof value === 'object') {
      if (value.label) return value.label;
      if (value.value !== undefined) return value.value;
      return JSON.stringify(value);
    }

    return String(value);
  };

  return (
    <>
      <div className="d-flex flex-wrap gap-3">
        {records.map((record) => {
          const thumbnailSrc = getThumbnailSrc(record);

          return (
            <div
              key={record.id}
              className="bg-white border rounded overflow-hidden"
              style={{
                width: config?.display_mode_options?.item_width || '220px',
                cursor: 'pointer',
              }}
            >
              {thumbnailSrc && (
                <div
                  style={{
                    height: config?.display_mode_options?.image_height || '150px',
                    background: '#f0f0f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                  }}
                  onClick={() => setExpandedRecord(record)}
                >
                  <img
                    src={thumbnailSrc}
                    alt={primaryField ? record.data[primaryField.name] : ''}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      objectFit: 'cover',
                    }}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                </div>
              )}
              <div className="p-2">
                {primaryField && (
                  <div
                    style={{ fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    title={record.data[primaryField.name]}
                  >
                    {record.data[primaryField.name] || t('unnamed-record')}
                  </div>
                )}
                {displayFields.map((f) => {
                  const value = record.data[f.name];
                  const isDescription = f.name.toLowerCase() === 'description';

                  if (isDescription && value) {
                    return (
                      <div key={f.name} className="d-flex align-items-center gap-1" style={{ fontSize: '0.85em' }}>
                        <span className="text-muted">{getFieldLabel(f.name)}: </span>
                        <OverlayTrigger
                          trigger={['hover', 'focus']}
                          placement="top"
                          overlay={
                            <Popover id={`popover-gallery-${record.id}-${f.name}`}>
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
                    <div key={f.name} style={{ fontSize: '0.85em' }}>
                      <span className="text-muted">{getFieldLabel(f.name)}: </span>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {formatValue(f, value)}
                      </span>
                    </div>
                  );
                })}
                <InteractionRowActions
                  interactions={config?.interactions}
                  recordData={record?.data}
                  recordId={record.id}
                  viewAs={viewAs}
                  getRoleRank={getRoleRank}
                  onInteraction={onInteraction}
                  className="d-flex flex-wrap gap-1 mt-2"
                />
                <div className="d-flex justify-content-end gap-2 mt-2">
                  <span className="link action" onClick={() => onEdit(record)}>
                    <EditIcon />
                  </span>
                  <span className="link action" onClick={() => onDelete(record.id)}>
                    <TrashIcon />
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <Modal show={!!expandedRecord} onHide={() => setExpandedRecord(null)} size="lg" className="migratis-modal">
        <Modal.Header className="migratis-modal-header">
          <span className="migratis-modal-icon"><ImageIcon /></span>
          <Modal.Title className="migratis-modal-title">
            {expandedRecord && primaryField
              ? expandedRecord.data[primaryField.name] || t('unnamed-record')
              : t('image-preview')}
          </Modal.Title>
          <button className="migratis-modal-close" onClick={() => setExpandedRecord(null)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 512 512"><path fill="currentColor" d="M400 145.7L366.3 112L256 222.7L145.7 112L112 145.7l110.3 110.3L112 366.3l33.7 33.7L256 333.3l110.3 110.3L400 366.3L289.7 256z"/></svg>
          </button>
        </Modal.Header>
        <Modal.Body className="text-center">
          {expandedRecord && (
            <img
              src={getThumbnailSrc(expandedRecord)}
              alt={primaryField ? expandedRecord.data[primaryField.name] : ''}
              style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain' }}
            />
          )}
          {expandedRecord && displayFields.map((f) => (
            <div key={f.name} className="mt-2">
              <strong>{getFieldLabel(f.name)}:</strong> {formatValue(f, expandedRecord.data[f.name])}
            </div>
          ))}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setExpandedRecord(null)}>
            {t('close')}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default GalleryDisplay;
