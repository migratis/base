// -----------------------------------------------------------------------------
// coerce — one cell of a spreadsheet, as the field it was mapped to.
//
// This is the browser's copy of `datasource/mapping.py`'s judgement, and it is
// a copy on purpose: the file is parsed where it was picked, so the reading of
// `"2,800,000"` has to happen here whether the row is going to the sandbox or
// to a generated application's own API.
//
// The rules are that module's, unchanged, because each of them is a production
// incident:
//
//   * **Strict grouping only.** `1,500` is fifteen hundred whichever convention
//     wrote it; `1,5` is one and a half in four of the languages this platform
//     speaks and fifteen in the fifth. One reading, or none.
//   * **One number only.** `"142 min"` reads one way; `"2h 22min"` reads as 2
//     or as 142, and a wrong number the owner cannot see is worse than a blank.
//   * **A leading number only.** `"$5"` would need a unit table.
//   * **`'N/A'` is nothing**, checked on the whole value before any type is
//     consulted, so a film called *Unknown Soldier* is still a film.
//   * **A blank is unknown, never zero.** An absent value is left out of the
//     payload entirely rather than sent as `0` or `''`.
//
// What it deliberately does NOT do is decide whether a value is *acceptable*.
// A cell that does not read as the field's type is passed through as written
// so the server refuses it and names the row — the import's failures come from
// the same validation the form's do, not from a second opinion held here.
// -----------------------------------------------------------------------------

import { LIST_JOIN } from './constants';

const SENTINELS = new Set([
  'n/a', 'n.a.', 'n\\a', '-', '--', '---', '—', '–', 'unknown', 'tbd',
]);

const GROUPED = /^-?\d{1,3}(?:,\d{3})+(?:\.\d+)?$/;
const LEADING_NUMBER = /^(-?\d+(?:\.\d+)?)\s*[^\d]*$/;
const TRUE_WORDS = new Set(['true', '1', 'yes', 'y', 'on']);
const FALSE_WORDS = new Set(['false', '0', 'no', 'n', 'off']);

/** Whether a cell holds nothing — empty, whitespace, or a sentinel. */
export function isBlank(value) {
  const text = String(value == null ? '' : value).trim();
  return !text || SENTINELS.has(text.toLowerCase());
}

/** The digits a cell means, as text, or `undefined`. */
export function numberText(value) {
  const text = String(value == null ? '' : value).trim();
  if (!text) return undefined;
  if (GROUPED.test(text)) return text.replace(/,/g, '');
  const match = LEADING_NUMBER.exec(text);
  return match ? match[1] : undefined;
}

function toBoolean(text) {
  const lower = text.toLowerCase();
  if (TRUE_WORDS.has(lower)) return true;
  if (FALSE_WORDS.has(lower)) return false;
  return undefined;
}

function toDate(text) {
  if (/^\d{4}$/.test(text)) return `${text}-01-01`;
  const head = text.replace(/\//g, '-').slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(head) && !Number.isNaN(Date.parse(head))
    ? head : undefined;
}

function toDatetime(text) {
  // An ISO datetime is kept whole; a bare date is a datetime at midnight,
  // which is what the form's own date control produces.
  if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(text)) return text.replace(' ', 'T');
  return toDate(text);
}

/** The option whose value or label is this cell, or undefined. */
function matchOption(text, options) {
  const lower = text.toLowerCase();
  const found = (options || []).find(
    (o) => String(o.value).toLowerCase() === lower
      || String(o.label ?? '').toLowerCase() === lower);
  return found ? found.value : undefined;
}

/**
 * One cell as the value a create request should carry, or `undefined`.
 *
 * @param {*} cell            what the file held
 * @param {object} field      `{name, field_type, choices, options}`
 *
 * `options` is how a relation is resolved: the host supplies the target's
 * `{value, label}` list — the same list its own form's select is built from —
 * and a cell matching a label becomes that id. Without options a relation
 * cannot be resolved here, and `mappableFields` does not offer one.
 */
export function coerceCell(cell, field = {}) {
  if (isBlank(cell)) return undefined;
  const text = String(cell).trim();
  const type = field.field_type || 'string';

  switch (type) {
    case 'integer': {
      const digits = numberText(text);
      if (digits === undefined) return text;
      const n = Math.trunc(Number(digits));
      return Number.isFinite(n) ? n : text;
    }
    case 'decimal': {
      const digits = numberText(text);
      if (digits === undefined) return text;
      const n = Number(digits);
      return Number.isFinite(n) ? n : text;
    }
    case 'boolean': {
      const bool = toBoolean(text);
      return bool === undefined ? text : bool;
    }
    case 'date':
      return toDate(text) ?? text;
    case 'datetime':
      return toDatetime(text) ?? text;
    case 'enum':
      // A file usually holds the LABEL. Matching it back to the stored value is
      // the difference between an import and a column of `invalid-choice`.
      return matchOption(text, field.choices) ?? text;
    case 'fk':
      return matchOption(text, field.options) ?? text;
    case 'm2m':
      return text.split(LIST_JOIN.trim())
        .map((part) => matchOption(part.trim(), field.options))
        .filter((v) => v !== undefined);
    default:
      return text;
  }
}

//: Field types a cell cannot carry. A file holds text; a `file` or an `image`
//: is bytes, and a `geo` value is a geometry a spreadsheet has no column for.
//: Named rather than silently skipped, so the modal can say why the field is
//: not in the list.
export const UNMAPPABLE_TYPES = new Set(['file', 'image', 'geo']);

/**
 * The fields of an entity a file column may be mapped to.
 *
 * A relation is offered only when its options were supplied — a dropdown with
 * nothing in it is the affordance without the thing it needs, which is the
 * mistake `direct_create → form` exists to repair one layer up.
 */
export function mappableFields(fields = []) {
  return fields.filter((f) => {
    if (UNMAPPABLE_TYPES.has(f.field_type)) return false;
    if (f.field_type === 'fk' || f.field_type === 'm2m') {
      return Array.isArray(f.options) && f.options.length > 0;
    }
    return true;
  });
}

/**
 * A first guess at which file column feeds which field.
 *
 * Exact name, then a folded comparison (`Release Year` → `release_year`), then
 * the field's description. Nothing fuzzier: a wrong auto-mapping that reads as
 * plausible is harder to spot in a review table than an unmapped column.
 */
export function guessMapping(columns = [], fields = []) {
  const fold = (s) => String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  const byKey = new Map();
  mappableFields(fields).forEach((f) => {
    [f.name, f.description].forEach((key) => {
      const folded = fold(key);
      if (folded && !byKey.has(folded)) byKey.set(folded, f.name);
    });
  });
  const mapping = {};
  const used = new Set();
  columns.forEach((column, index) => {
    const match = byKey.get(fold(column));
    if (match && !used.has(match)) {
      mapping[index] = match;
      used.add(match);
    }
  });
  return mapping;
}
