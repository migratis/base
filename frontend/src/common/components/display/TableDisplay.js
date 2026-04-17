import Table from 'react-bootstrap/Table';
import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
} from 'react-icons/io5';

const TableDisplay = ({
  entity,
  records,
  relOptions = {},
  config = {},
  onEdit,
  onDelete,
  t,
  sortBy = '',
  sortDir = 'asc',
  onSort,
  sortableFields = [],
}) => {
  if (!records || records.length === 0) {
    return null;
  }

  const fieldsConfig = config?.fields || {};

  const tval = (key, fallback) => t ? t(key, fallback) : fallback || key;

  const getFieldLabel = (fieldName) => {
    return fieldsConfig[fieldName]?.label || fieldName;
  };

  // Primary-identifier field names — always shown first
  const _PRIMARY_NAMES = ['name', 'label', 'title', 'code', 'reference', 'ref', 'number', 'slug'];
  const displayLabelFields = config?.display_label_fields || [];

  const isPrimaryField = (fieldName) => {
    if (displayLabelFields.includes(fieldName)) return true;
    const lower = fieldName?.toLowerCase() || '';
    return _PRIMARY_NAMES.some((p) => lower === p || lower.endsWith('_' + p));
  };

  const getFieldOrder = () => {
    const fields = entity.fields.map((f) => ({ type: 'field', ...f }));
    const rels   = (entity.relationships || []).map((r) => ({ type: 'relationship', ...r }));
    const primary = fields.filter((f) => isPrimaryField(f.name));
    const rest    = fields.filter((f) => !isPrimaryField(f.name));
    return [...primary, ...rest, ...rels];
  };

  const columns = getFieldOrder();
  const maxColumns = config?.display_mode_options?.max_columns || 6;
  const displayColumns = columns.slice(0, maxColumns);

  const resolveRelLabel = (fieldName, value) => {
    if (!value) return '—';
    const opts = relOptions[fieldName] || [];
    if (Array.isArray(value)) {
      return value.map((id) => {
        const opt = opts.find((o) => o.value === id);
        return opt ? opt.label : `#${id}`;
      }).join(', ') || '—';
    }
    const opt = opts.find((o) => o.value === value);
    return opt ? opt.label : `#${value}`;
  };

  const _SCALE_LABELS = {
    nm2: 'nm²', um2: 'μm²', mm2: 'mm²', cm2: 'cm²', dm2: 'dm²',
    m2: 'm²', dam2: 'dam²', hm2: 'hm²', km2: 'km²',
  };

  const formatValue = (field, value) => {
    if (value === null || value === undefined) return '—';
    // Handle {label, value} objects from select fields
    if (typeof value === 'object' && value !== null) {
      return value.label || value.value || '—';
    }
    const renderAs = fieldsConfig[field.name]?.render_as;
    // Shape field — show computed surface instead of raw JSON
    if (renderAs === 'shape' || (typeof value === 'string' && value.startsWith('{"shape"'))) {
      try {
        const parsed = JSON.parse(value);
        const n = parseFloat(parsed.surface) || 0;
        if (n === 0) return '—';
        const label = _SCALE_LABELS[parsed.scale] || parsed.scale || '';
        const formatted = n < 0.01
          ? n.toExponential(3)
          : n % 1 === 0 ? n.toString() : parseFloat(n.toFixed(4)).toString();
        return `${formatted} ${label}`;
      } catch { /* fall through */ }
    }
    if (field.field_type === 'boolean') {
      return value ? tval('true', 'Yes') : tval('false', 'No');
    }
    // Date/datetime — strip time portion unless render_as is explicitly 'datetime' or 'time'
    if (field.field_type === 'date' || field.field_type === 'datetime') {
      if (!value) return '—';
      if (renderAs === 'time') return String(value).slice(11, 16);
      if (renderAs === 'datetime') {
        const d = new Date(value);
        return isNaN(d) ? String(value) : d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      const d = new Date(value);
      return isNaN(d) ? String(value).slice(0, 10) : d.toLocaleDateString();
    }
    return String(value);
  };

  const _isHexColor = (v) => typeof v === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(v.trim());

  const renderCellValue = (field, value) => {
    const str = formatValue(field, value);
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
    return str;
  };

  return (
    <div className="table-responsive border rounded">
      <Table hover size="sm" className="mb-0">
        <thead className="table-light">
          <tr>
            <th style={{ width: '80px' }}></th>
            {displayColumns.map((col) => {
              const fieldKey = col.type === 'field' ? col.name : col.field_name;
              const isSortable = col.type === 'field' && sortableFields.includes(col.name) && !!onSort;
              const isActive   = sortBy === col.name;
              return (
                <th
                  key={fieldKey}
                  onClick={isSortable ? () => onSort(col.name) : undefined}
                  style={isSortable ? { cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap' } : undefined}
                >
                  {col.type === 'field' ? getFieldLabel(col.name) : col.related_entity}
                  {isSortable && (
                    <span className="ms-1 text-muted" style={{ fontSize: '0.75em' }}>
                      {isActive ? (sortDir === 'asc' ? '▲' : '▼') : '⇅'}
                    </span>
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id} className="align-middle">
              <td>
                <div className="d-flex gap-1">
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
              </td>
              {displayColumns.map((col) => (
                <td
                  key={col.name || col.field_name}
                  style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                  title={col.type === 'field'
                    ? formatValue(col, record.data[col.name])
                    : resolveRelLabel(col.field_name, record.data[col.field_name])}
                >
                  {col.type === 'field'
                    ? renderCellValue(col, record.data[col.name])
                    : resolveRelLabel(col.field_name, record.data[col.field_name])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
};

export default TableDisplay;
