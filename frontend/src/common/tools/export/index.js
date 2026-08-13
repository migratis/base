// -----------------------------------------------------------------------------
// exportData — the one door.
//
// Everything above it (a toolbar button, a custom component, a generated app's
// list page) hands over the same thing: a table and what to call the file. What
// it does NOT do is fetch, decide who may read a row, or charge for anything:
// it is handed rows that a server already served to this viewer under this
// role, and turning them into a file is deterministic and free.
//
// It never throws into a render. A caller is frequently a component's onClick,
// and a rejected promise there ends up as an unhandled rejection with nothing
// on screen; so every failure resolves as `{ok: false, reason}` and the caller
// decides what to say.
// -----------------------------------------------------------------------------

import download from 'downloadjs';
import { cellValue } from './values';
import { buildCsv, CSV_MIME } from './csv';

export { exportColumns } from './columns';
export { formatCellValue, cellValue, relationLabels, cellType, EMPTY } from './values';

// A hard ceiling on what one export may carry. Not a security boundary — the
// rows were already served — but a browser that is asked to hold a hundred
// thousand rows and build a PDF from them stops responding, and a tab that
// dies mid-export tells the user nothing.
export const EXPORT_MAX_ROWS = 5000;

export const EXPORT_FORMATS = ['xlsx', 'csv', 'pdf'];

const _EXT = { xlsx: 'xlsx', csv: 'csv', pdf: 'pdf' };

/**
 * Turn served records into the cell matrix the writers take.
 *
 * @param {Array} records   `[{id, data}]` as every list endpoint returns
 * @param {Array} columns   from `exportColumns`
 * @param {object} opts     `{config, relOptions, t}`
 */
export function buildRows(records, columns, opts = {}) {
  const { config = {}, relOptions = {}, t } = opts;
  const fieldsConfig = config?.fields || {};
  return (records || []).map((record) => {
    const data = record?.data || record || {};
    return columns.map((col) => {
      if (col.relation) {
        return cellValue({ name: col.key }, data[col.key], {
          relationOptions: relOptions[col.key] || [], t,
        });
      }
      // A caller with no entity schema (the generic `Entities` list) declares
      // its columns by hand and may name a `type` — which is what puts a real
      // number or a real date in the spreadsheet instead of a string shaped
      // like one.
      const field = col.field || { name: col.key, field_type: col.type };
      return cellValue(field, data[col.key], {
        fieldConfig: fieldsConfig[col.key], t,
      });
    });
  });
}

// A filename has to survive Windows, macOS and a Content-Disposition header.
export function safeFilename(name) {
  return String(name || 'export')
    .replace(/[\\/:*?"<>|]+/g, '-')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^[-_.]+|[-_.]+$/g, '')
    .slice(0, 120) || 'export';
}

/** `<App>_<Entity>_<YYYY-MM-DD>` — the caller supplies the parts it has. */
export function exportFilename({ app, entity, date = new Date() }) {
  const day = new Date(date).toISOString().slice(0, 10);
  return safeFilename([app, entity, day].filter(Boolean).join('_'));
}

/**
 * Write a table to a file the browser downloads.
 *
 * @param {object} spec
 * @param {'xlsx'|'csv'|'pdf'} spec.format
 * @param {string}   spec.filename   without extension
 * @param {string}   spec.title      document heading (PDF) / sheet name (XLSX)
 * @param {Array}    spec.columns    `[{key, label}]` — or `exportColumns` output
 * @param {Array}    spec.rows       cell matrix from `buildRows`
 * @param {object}   spec.meta       `{app, filters, search, exportedAt}` — printed
 *                                   in the PDF header, because a filtered export
 *                                   that does not say so is a false document
 * @param {function} spec.t          i18n, for the PDF's own words
 * @returns {Promise<{ok: boolean, reason?: string, rows?: number}>}
 */
export async function exportData(spec = {}) {
  const {
    format = 'xlsx',
    filename = 'export',
    title = '',
    columns = [],
    rows = [],
    meta = {},
    t,
  } = spec;

  if (!EXPORT_FORMATS.includes(format)) {
    return { ok: false, reason: 'export-format-unknown' };
  }
  if (!columns.length) {
    return { ok: false, reason: 'export-nothing-to-export' };
  }
  if (rows.length > EXPORT_MAX_ROWS) {
    // Refuse out loud. Writing the first 5 000 of 40 000 rows into a file that
    // looks complete is the one outcome worse than not exporting.
    return { ok: false, reason: 'export-too-many-rows', limit: EXPORT_MAX_ROWS };
  }

  const headers = columns.map((c) => c.label ?? c.key);
  const name = `${safeFilename(filename)}.${_EXT[format]}`;

  try {
    if (format === 'csv') {
      download(new Blob([buildCsv({ headers, rows })], { type: CSV_MIME }), name, CSV_MIME);
      return { ok: true, rows: rows.length };
    }

    if (format === 'xlsx') {
      // Loaded on demand: a user who never exports never pays for the writer.
      const { buildXlsx, XLSX_MIME } = await import('./xlsx');
      const bytes = await buildXlsx({ sheetName: title || filename, headers, rows });
      download(new Blob([bytes], { type: XLSX_MIME }), name, XLSX_MIME);
      return { ok: true, rows: rows.length };
    }

    const { buildPdf, PDF_MIME, PDF_UNAVAILABLE } = await import('./pdf');
    const blob = await buildPdf({ title, headers, rows, meta, t });
    if (blob === PDF_UNAVAILABLE) {
      return { ok: false, reason: 'export-pdf-unavailable' };
    }
    download(blob, name, PDF_MIME);
    return { ok: true, rows: rows.length };
  } catch (err) {
    // Never into a render. The caller reports; the console keeps the detail.
    console.warn('[export] failed', err);   // eslint-disable-line no-console
    return { ok: false, reason: 'export-failed' };
  }
}

export default exportData;
