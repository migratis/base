// -----------------------------------------------------------------------------
// columns — which columns an export carries, in what order, under what label.
//
// A display truncates: TableDisplay stops at `max_columns` (6 by default),
// ListDisplay shows a primary field and two more. That is a decision about a
// NARROW SCREEN, and a spreadsheet is not one — an export that inherited it
// would silently drop most of the data the user asked for. So the export takes
// **every readable field**, in the display's own order first (so the columns
// the user recognises come first) and then the rest.
//
// "Readable" needs no work here and that is the point: the rows being exported
// are the rows the server served, already masked per role. A field the viewer
// may not read never arrives, so it never becomes a column.
// -----------------------------------------------------------------------------

// The names a row display treats as a record's identity — mirrored from
// TableDisplay so both put the same columns first.
const _PRIMARY_NAMES = ['name', 'label', 'title', 'code', 'reference', 'ref', 'number', 'slug'];

const _isPrimary = (fieldName, displayLabelFields = []) => {
  if (displayLabelFields.includes(fieldName)) return true;
  const lower = fieldName?.toLowerCase() || '';
  return _PRIMARY_NAMES.some((p) => lower === p || lower.endsWith(`_${p}`));
};

/**
 * Build the column list for an entity.
 *
 * @param {object} entity  `{name, fields: [], relationships: []}`
 * @param {object} config  the entity's sandbox/entity config
 * @param {object} opts
 * @param {Set<string>|null} opts.hiddenFields  names the config marks invisible
 * @returns {Array<{key, label, field, relation}>}
 *   `field` is the field descriptor for a plain column; `relation` is the
 *   relationship descriptor for a linked one. Exactly one of the two is set.
 */
export function exportColumns(entity, config = {}, opts = {}) {
  const fieldsConfig = config?.fields || {};
  const relsConfig = config?.relationships || {};
  const displayLabelFields = config?.display_label_fields || [];
  const { hiddenFields = null } = opts;

  const label = (name, fallback) => fieldsConfig[name]?.label || fallback || name;

  const fields = (entity?.fields || []).filter((f) => {
    if (hiddenFields && hiddenFields.has(f.name)) return false;
    // `visible: false` is the config saying this column is not part of the
    // record's presentation. An export honours it: it is the owner's decision
    // about what the entity shows, not a screen-width compromise.
    return fieldsConfig[f.name]?.visible !== false;
  });

  const primary = fields.filter((f) => _isPrimary(f.name, displayLabelFields));
  const rest = fields.filter((f) => !_isPrimary(f.name, displayLabelFields));

  const fieldColumns = [...primary, ...rest].map((f) => ({
    key: f.name,
    label: label(f.name),
    field: f,
    relation: null,
  }));

  const relColumns = (entity?.relationships || []).map((r) => ({
    key: r.field_name,
    label: relsConfig[r.field_name]?.label || r.related_entity || r.field_name,
    field: null,
    relation: r,
  }));

  return [...fieldColumns, ...relColumns];
}

export default exportColumns;
