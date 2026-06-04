import Badge from 'react-bootstrap/Badge';
import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
} from 'react-icons/io5';
import InteractionRowActions from '../InteractionRowActions';

const KanbanDisplay = ({
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
  if (!records || records.length === 0) {
    return null;
  }

  const fieldsConfig = config?.fields || {};
  const displayModeOptions = config?.display_mode_options || {};

  const tval = (key, fallback) => t ? t(key, fallback) : fallback || key;

  const statusField = displayModeOptions.status_field
    ? entity.fields.find((f) => f.name === displayModeOptions.status_field)
    : entity.fields.find((f) =>
        ['status', 'state', 'stage', 'phase', 'category', 'type'].includes(f.name.toLowerCase())
      );

  const statusOptions = displayModeOptions.status_options ||
    (statusField?.field_type === 'fk' || statusField?.field_type === 'string'
      ? [...new Set(records.map((r) => r.data[statusField?.name]).filter(Boolean))]
      : ['To Do', 'In Progress', 'Done']);

  const getFieldLabel = (fieldName) => {
    return fieldsConfig[fieldName]?.label || fieldName;
  };

  const getPrimaryField = () => {
    return entity.fields.find((f) =>
      f.name === 'name' || f.name === 'title' || f.name === 'description'
    );
  };

  const primaryField = getPrimaryField();

  const formatValue = (value) => {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'object' && value !== null) {
      return value.label || value.value || '—';
    }
    return String(value);
  };

  const getColumnTitle = (status) => {
    if (displayModeOptions.status_labels?.[status]) {
      return displayModeOptions.status_labels[status];
    }
    return status;
  };

  const getColumnColor = (status) => {
    const colors = displayModeOptions.status_colors || {};
    return colors[status] || 'secondary';
  };

  const getRecordsForColumn = (status) => {
    if (!statusField) {
      return records;
    }
    return records.filter((r) => r.data[statusField.name] === status);
  };

  return (
    <div className="d-flex overflow-auto gap-3 pb-3" style={{ minHeight: '400px' }}>
      {statusOptions.map((status) => {
        const columnRecords = getRecordsForColumn(status);
        return (
          <div
            key={status}
            style={{
              minWidth: '280px',
              maxWidth: '320px',
              flex: '0 0 280px',
              background: '#f8f9fa',
              borderRadius: '0.5rem',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              className="d-flex justify-content-between align-items-center p-2"
              style={{ borderBottom: '2px solid', borderColor: `var(--bs-${getColumnColor(status)})` }}
            >
              <span style={{ fontWeight: 'bold' }}>{getColumnTitle(status)}</span>
              <Badge bg={getColumnColor(status)}>{columnRecords.length}</Badge>
            </div>
            <div className="flex-grow-1 overflow-auto p-2" style={{ minHeight: '200px' }}>
              {columnRecords.map((record) => (
                <div
                  key={record.id}
                  className="bg-white border rounded p-2 mb-2"
                  style={{ cursor: onEdit ? 'pointer' : 'default' }}
                  onClick={onEdit ? () => onEdit(record) : undefined}
                >
                  {primaryField && (
                    <div style={{ fontWeight: '500', marginBottom: '0.5rem' }}>
                      {formatValue(record.data[primaryField.name]) || tval('unnamed-record', 'Unnamed')}
                    </div>
                  )}
                  <div style={{ fontSize: '0.85em', color: '#666' }}>
                    {entity.fields
                      .filter((f) => f !== primaryField && fieldsConfig[f.name])
                      .slice(0, 2)
                      .map((f) => (
                        <div key={f.name}>
                          <span className="text-muted">{getFieldLabel(f.name)}: </span>
                          {formatValue(record.data[f.name])}
                        </div>
                      ))}
                  </div>
                  <InteractionRowActions
                    interactions={config?.interactions}
                    recordData={record?.data}
                    recordId={record.id}
                    viewAs={viewAs}
                    getRoleRank={getRoleRank}
                    onInteraction={onInteraction}
                    className="d-flex flex-wrap gap-1 mt-2"
                  />
                  {(onEdit || onDelete) && (
                    <div className="d-flex justify-content-end gap-1 mt-2">
                      {onEdit && (
                        <span className="link action" onClick={(e) => { e.stopPropagation(); onEdit(record); }}>
                          <EditIcon />
                        </span>
                      )}
                      {onDelete && (
                        <span className="link action" onClick={(e) => { e.stopPropagation(); onDelete(record.id); }}>
                          <TrashIcon />
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {columnRecords.length === 0 && (
                <div className="text-center text-muted p-3" style={{ fontSize: '0.85em' }}>
                  {tval('no-records-in-column', 'No records')}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default KanbanDisplay;
