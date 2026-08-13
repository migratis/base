// -----------------------------------------------------------------------------
// values — the one reading of a cell.
//
// Every row display formats the same stored value into text, and before this
// module each of them had its own copy: TableDisplay knew about shapes and geo,
// ListDisplay knew about geo but not shapes and truncated at 40 characters,
// GalleryDisplay knew about neither. An export added on top of that would have
// been a fourth opinion about what a cell says — the shape of bug that let a
// formula target be hidden by codegen, shown by the sandbox form, and computed
// by neither.
//
// So: **this module owns MEANING, a display owns FITTING.** The canonical
// string is never truncated, never wrapped in markup and never localised
// beyond the words a value genuinely carries (Yes/No, "points"); a display
// truncates it, decorates it, or replaces it with a swatch or an <img> as its
// own layout requires.
//
// `cellValue` is the same reading with its TYPE kept: a spreadsheet that cannot
// sum a column is not an export, so a number reaches the writer as a number and
// a date as a Date, while everything whose reading is a sentence reaches it as
// that sentence.
// -----------------------------------------------------------------------------

import { geoSummary, isGeoField } from '../../fields/geoSummary';

// The marker every display already shows for "nothing here". Shared so the
// export cannot invent a different blank.
export const EMPTY = '—';

// Surface units for a `shape` value, which stores its own scale.
const _SCALE_LABELS = {
  nm2: 'nm²', um2: 'μm²', mm2: 'mm²', cm2: 'cm²', dm2: 'dm²',
  m2: 'm²', dam2: 'dam²', hm2: 'hm²', km2: 'km²',
};

const _NUMERIC_TYPES = new Set(['integer', 'decimal']);

// A render_as whose reading is not the raw value, whatever the field type says.
const _NON_NUMERIC_RENDERERS = new Set(['shape', 'color', 'image', 'images', 'map']);

const _tval = (t, key, fallback) => (t ? t(key, fallback) : fallback);

/**
 * Resolve a relationship value (an id, or a list of them) to the labels the
 * displays show. Returns a list so a caller can join it or render each label
 * as its own badge; an unresolvable id is kept visibly as `#<id>` rather than
 * dropped, because a silently missing link reads as "no link".
 */
export function relationLabels(value, options = []) {
  if (value === null || value === undefined || value === '') return [];
  const opts = Array.isArray(options) ? options : [];
  const label = (id) => {
    const opt = opts.find((o) => o.value === id);
    return opt ? opt.label : `#${id}`;
  };
  if (Array.isArray(value)) return value.map(label);
  return [label(value)];
}

/**
 * What kind of cell this column holds — 'number', 'date', 'datetime' or 'text'.
 * Read by the writers to decide whether to emit a typed cell; a `render_as`
 * that replaces the value with a rendering of its own always wins, because a
 * shape's stored JSON is not the number the user reads.
 */
export function cellType(field, fieldConfig) {
  const renderAs = fieldConfig?.render_as;
  if (renderAs && _NON_NUMERIC_RENDERERS.has(renderAs)) return 'text';
  const type = field?.field_type;
  if (_NUMERIC_TYPES.has(type)) return 'number';
  if (type === 'date') return 'date';
  if (type === 'datetime') return 'datetime';
  return 'text';
}

function _formatShape(raw, t) {
  try {
    const parsed = JSON.parse(raw);
    const n = parseFloat(parsed.surface) || 0;
    if (n === 0) return EMPTY;
    const label = _SCALE_LABELS[parsed.scale] || parsed.scale || '';
    const formatted = n < 0.01
      ? n.toExponential(3)
      : n % 1 === 0 ? n.toString() : parseFloat(n.toFixed(4)).toString();
    return `${formatted} ${label}`.trim();
  } catch {
    return _tval(t, 'shape-cell', 'Shape');
  }
}

function _formatImages(raw, t) {
  try {
    const arr = JSON.parse(raw);
    const n = Array.isArray(arr) ? arr.filter(Boolean).length : 0;
    if (!n) return EMPTY;
    if (n === 1) return _tval(t, 'image-cell', 'Image');
    return `${n} ${_tval(t, 'images-cell', 'images')}`;
  } catch {
    return _tval(t, 'image-cell', 'Image');
  }
}

/**
 * The canonical text reading of one stored value.
 *
 * @param {object} field         the entity field descriptor ({name, field_type})
 * @param {*}      value         as stored in `record.data`
 * @param {object} opts
 * @param {object} opts.fieldConfig  this field's entry in `config.fields`
 * @param {function} opts.t          i18n `t(key, fallback)`; optional
 * @param {Array}  opts.relationOptions  options for a relationship column
 * @param {string} opts.empty        marker for an absent value
 * @returns {string} never markup, never truncated
 */
export function formatCellValue(field, value, opts = {}) {
  const { fieldConfig, t, relationOptions, empty = EMPTY } = opts;

  if (relationOptions) {
    const labels = relationLabels(value, relationOptions);
    return labels.length ? labels.join(', ') : empty;
  }

  if (value === null || value === undefined || value === '') return empty;

  // A select field can hand back the whole option object. An array reaching
  // here is a relationship column that was not given its options, and it has no
  // reading at all — never its raw ids.
  if (typeof value === 'object') {
    return String(value.label || value.value || empty);
  }

  const renderAs = fieldConfig?.render_as;
  const raw = typeof value === 'string' ? value.trim() : String(value);

  // A geo value is read through the one summary every text surface shares — the
  // stored GeoJSON is not a value a user can read, and app 2 shipped four
  // tables that printed it verbatim.
  if (isGeoField(field, fieldConfig)) {
    const summary = geoSummary(value);
    if (!summary) return empty;
    return summary.text || `${summary.count} ${_tval(t, 'geo-points', 'points')}`;
  }

  if (renderAs === 'shape' || raw.startsWith('{"shape"')) {
    return _formatShape(raw, t);
  }

  if (renderAs === 'images' || (field?.field_type === 'image' && raw.startsWith('['))) {
    return _formatImages(raw, t);
  }

  // An image cell never carries its data URI: it is unreadable on a page, it is
  // useless in a spreadsheet, and it is tens of kilobytes per row.
  if (renderAs === 'image' || field?.field_type === 'image' || field?.field_type === 'file') {
    if (!raw) return empty;
    if (raw.startsWith('data:') || field?.field_type === 'image') {
      return _tval(t, 'image-cell', 'Image');
    }
    return raw;
  }

  if (field?.field_type === 'boolean') {
    return value ? _tval(t, 'true', 'Yes') : _tval(t, 'false', 'No');
  }

  // The time is shown only when the config asks for it. That is the displays'
  // long-standing rule and it is preserved here deliberately — but it is a
  // PRESENTATION rule, so `cellValue` still hands a writer the full timestamp
  // (see below): a spreadsheet loses nothing that the table merely does not show.
  if (field?.field_type === 'date' || field?.field_type === 'datetime') {
    if (renderAs === 'time') return String(value).slice(11, 16);
    const d = new Date(value);
    if (renderAs === 'datetime') {
      return isNaN(d)
        ? String(value)
        : `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
    return isNaN(d) ? String(value).slice(0, 10) : d.toLocaleDateString();
  }

  return String(value);
}

/**
 * The same reading, with its type kept, for the writers.
 *
 * Returns `{type, value, text}`: `text` is always the string
 * `formatCellValue` produced, `value` is what the cell should HOLD — a Number
 * for a numeric column, a Date for a date column, the text otherwise. A value
 * that claims a type it cannot honour (a number field holding "n/a", a date
 * that will not parse) degrades to text rather than to a fabricated 0 or an
 * Invalid Date: an unknown is never an answer.
 */
export function cellValue(field, value, opts = {}) {
  const text = formatCellValue(field, value, opts);
  const asText = (v) => ({ type: 'text', value: v, text });

  if (opts.relationOptions) return asText(text === EMPTY ? '' : text);
  if (value === null || value === undefined || value === '') return asText('');

  const type = cellType(field, opts.fieldConfig);

  if (type === 'number') {
    const n = typeof value === 'number' ? value : parseFloat(String(value));
    if (Number.isFinite(n) && String(value).trim() !== '') {
      return { type: 'number', value: n, text };
    }
    return asText(String(value));
  }

  if (type === 'date' || type === 'datetime') {
    const d = new Date(value);
    if (!isNaN(d)) return { type, value: d, text };
    return asText(String(value));
  }

  return asText(text === EMPTY ? '' : text);
}

export default formatCellValue;
