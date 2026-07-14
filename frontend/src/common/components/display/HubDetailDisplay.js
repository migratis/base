import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Image from 'react-bootstrap/Image';
import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
  IoImageOutline as ImagePlaceholderIcon,
} from 'react-icons/io5';
import InteractionRowActions from '../InteractionRowActions';

/**
 * HubDetailDisplay — the deterministic "unified hub" composite
 * (GAP_ANALYSIS_agent_lane_poc15.md §1). Renders ONE hub record as a detail
 * panel — cover photo + every visible field + relationship labels + workflow
 * action buttons + edit/delete — with a compact picker to switch records. The
 * hub's embedded children render BENEATH this panel through the existing
 * EmbeddedChildList machinery in Sandbox.js, so the whole page reads as photo +
 * fields + children + actions on one surface.
 *
 * It is the sanctioned fallback the composite-display rail (readiness
 * `hub_entity_plain_display`, now blocking) accepts when the agent doesn't
 * author a custom_display, and the auto-degrade target when a supplied
 * custom_display fails to render. No AI authoring, sandbox/codegen parity by
 * construction.
 */
const HubDetailDisplay = ({
  entity,
  records,
  relOptions = {},
  config = {},
  onEdit,
  onDelete,
  onInteraction,
  viewAs,
  getRoleRank,
  selectedRecordId = null,
  onSelectRecord,
  t,
}) => {
  if (!records || records.length === 0) return null;

  const tval = (key, fallback) => (t ? t(key, fallback) : fallback || key);
  const fieldsConfig = config?.fields || {};
  const relationshipsConfig = config?.relationships || {};
  const displayOptions = config?.display_mode_options || {};
  const thumbnailFieldName = displayOptions?.thumbnail_field;

  const imageFieldNames = new Set(
    entity.fields
      .filter((f) => f.field_type === 'file' || ['image', 'images'].includes(fieldsConfig[f.name]?.render_as))
      .map((f) => f.name),
  );
  if (thumbnailFieldName) imageFieldNames.add(thumbnailFieldName);

  const getFieldLabel = (fieldName) => fieldsConfig[fieldName]?.label || fieldName;

  const getAllImages = (record) => {
    const out = [];
    const seen = new Set();
    const push = (v) => {
      if (typeof v !== 'string' || seen.has(v)) return;
      if (v.startsWith('data:') || v.startsWith('http') || v.startsWith('/')) {
        seen.add(v);
        out.push(v);
      }
    };
    const ordered = Array.from(new Set([thumbnailFieldName, ...imageFieldNames].filter(Boolean)));
    for (const fname of ordered) {
      const value = record.data?.[fname];
      if (!value) continue;
      if (typeof value === 'string' && value.startsWith('[')) {
        try {
          const arr = JSON.parse(value);
          if (Array.isArray(arr)) arr.forEach(push);
        } catch { /* not a JSON array — ignore */ }
      } else {
        push(value);
      }
    }
    return out;
  };

  const getDisplayValue = (field, value) => {
    if (value === null || value === undefined || value === '') return null;
    if (field.field_type === 'boolean') return value ? tval('true', 'Yes') : tval('false', 'No');
    const options = fieldsConfig[field.name]?.options;
    if (Array.isArray(options)) {
      const option = options.find((o) => o.value === value);
      if (option) return option.label || option.value;
    }
    if (field.field_type === 'date' || field.field_type === 'datetime') {
      const d = new Date(value);
      if (isNaN(d)) return String(value).slice(0, 10);
      return field.field_type === 'datetime' ? d.toLocaleString() : d.toLocaleDateString();
    }
    if (typeof value === 'object') {
      if (value.label) return value.label;
      if (value.value !== undefined) return value.value;
      return JSON.stringify(value);
    }
    return String(value);
  };

  const resolveRelLabel = (fieldName, value) => {
    if (!value) return null;
    const opts = relOptions[fieldName] || [];
    const list = Array.isArray(value) ? value : [value];
    return list.map((id) => {
      const opt = opts.find((o) => o.value === id);
      return opt ? opt.label : `#${id}`;
    });
  };

  const _PRIMARY_NAMES = ['name', 'label', 'title', 'code', 'reference', 'ref', 'number', 'slug'];
  const displayLabelFields = config?.display_label_fields || [];
  const nonImageFields = entity.fields.filter((f) => !imageFieldNames.has(f.name));
  const primaryField = nonImageFields.find((f) => {
    if (displayLabelFields.includes(f.name)) return true;
    const lower = f.name?.toLowerCase() || '';
    return _PRIMARY_NAMES.some((p) => lower === p || lower.endsWith('_' + p));
  }) || nonImageFields[0];

  const labelOf = (record) => {
    const v = primaryField ? getDisplayValue(primaryField, record.data?.[primaryField.name]) : null;
    return v || tval('unnamed-record', 'Untitled');
  };

  const selected = records.find((r) => r.id === selectedRecordId) || records[0];
  const images = getAllImages(selected);
  const detailFields = nonImageFields.filter((f) => f !== primaryField);

  return (
    <div>
      {/* Record picker — deterministic composite still lets the viewer choose
          which hub record's detail (and its embedded children) is on screen. */}
      {records.length > 1 && (
        <div className="d-flex flex-wrap gap-2 mb-3">
          {records.map((r) => (
            <Button
              key={r.id}
              size="sm"
              variant={r.id === selected.id ? 'primary' : 'outline-secondary'}
              onClick={() => onSelectRecord && onSelectRecord(r.id)}
            >
              {labelOf(r)}
            </Button>
          ))}
        </div>
      )}

      <div className="card shadow-sm">
        <div className="row g-0">
          <div className="col-md-5">
            <div
              style={{ minHeight: 220, height: '100%', background: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              {images.length > 0 ? (
                <Image
                  src={images[0]}
                  style={{ width: '100%', height: '100%', maxHeight: 360, objectFit: 'cover' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              ) : (
                <ImagePlaceholderIcon style={{ fontSize: '3rem', color: '#ccc' }} />
              )}
            </div>
          </div>
          <div className="col-md-7">
            <div className="card-body">
              <h4 className="card-title mb-3">{labelOf(selected)}</h4>
              {detailFields.map((field) => {
                const val = getDisplayValue(field, selected.data?.[field.name]);
                if (val === null) return null;
                return (
                  <div key={field.name} className="mb-2">
                    <span className="text-muted small">{getFieldLabel(field.name)}: </span>
                    <span>{val}</span>
                  </div>
                );
              })}
              {(entity.relationships || []).map((rel) => {
                const labels = resolveRelLabel(rel.field_name, selected.data?.[rel.field_name]);
                if (!labels || labels.length === 0) return null;
                const relLabel = relationshipsConfig[rel.field_name]?.label || rel.field_name;
                return (
                  <div key={rel.field_name} className="mb-2">
                    <span className="text-muted small">{relLabel}: </span>
                    {labels.map((label, i) => (
                      <Badge key={i} bg="secondary" className="me-1">{label}</Badge>
                    ))}
                  </div>
                );
              })}
              <InteractionRowActions
                interactions={config?.interactions}
                recordData={selected?.data}
                recordId={selected.id}
                viewAs={viewAs}
                getRoleRank={getRoleRank}
                onInteraction={onInteraction}
                className="d-flex flex-wrap gap-2 mt-3 pt-2 border-top"
              />
              {(onEdit || onDelete) && (
                <div className="d-flex gap-3 mt-3 pt-2 border-top">
                  {onEdit && (
                    <span className="link action" onClick={() => onEdit(selected)} title={tval('edit', 'Edit')}>
                      <EditIcon /> {tval('edit', 'Edit')}
                    </span>
                  )}
                  {onDelete && (
                    <span className="link action text-danger" onClick={() => onDelete(selected.id)} title={tval('delete', 'Delete')}>
                      <TrashIcon /> {tval('delete', 'Delete')}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HubDetailDisplay;
