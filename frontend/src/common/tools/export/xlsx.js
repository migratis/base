// -----------------------------------------------------------------------------
// xlsx — a minimal .xlsx writer.
//
// An .xlsx is a zip of six small XML parts, and `jszip` was already declared in
// both repos' package.json (and imported nowhere). So this is written here
// rather than pulled in: npm's `xlsx` is a stale build carrying advisories, and
// `exceljs` is about a megabyte to write a flat sheet. What we need is a flat
// sheet.
//
// The one thing a hand-rolled writer must get right is TYPES. A spreadsheet
// whose numbers are strings cannot be summed and whose dates are text cannot be
// sorted — at which point the export is a screenshot with extra steps. So a
// number is written as `<v>`, a date as Excel's day serial with a date format
// attached, and only what genuinely reads as a sentence is written as text.
//
// Strings are written INLINE (`t="inlineStr"`) rather than through a shared
// string table: it costs a few bytes per repeated value and removes a whole
// index that could disagree with the sheet.
// -----------------------------------------------------------------------------

import JSZip from 'jszip';

const _NS_MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main';
const _NS_REL_DOC = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const _NS_REL_PKG = 'http://schemas.openxmlformats.org/package/2006/relationships';

// Style indexes into `cellXfs` below. Kept as names because a bare `s="3"` in
// the sheet is unreadable and the order of that list is load-bearing.
const STYLE_DEFAULT  = 0;
const STYLE_HEADER   = 1;
const STYLE_DATE     = 2;
const STYLE_DATETIME = 3;

// XML 1.0 cannot represent these at all — not even as a character reference —
// so a value carrying one has to lose it or the file will not open.
// Built from escapes rather than written as a literal so this source file
// itself stays free of the control characters it is describing.
// The disable is on the pattern itself, and naming these IS the point: the rule
// exists to catch a control character matched by ACCIDENT, which is the opposite
// of a writer whose job is to strip them.
// eslint-disable-next-line no-control-regex
const _INVALID_XML = new RegExp('[\\u0000-\\u0008\\u000B\\u000C\\u000E-\\u001F\\uFFFE\\uFFFF]', 'g');

function xmlEscape(value) {
  return String(value)
    .replace(_INVALID_XML, '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** 0 → A, 25 → Z, 26 → AA. Spreadsheet columns are bijective base-26. */
export function columnRef(index) {
  let n = index;
  let ref = '';
  do {
    ref = String.fromCharCode(65 + (n % 26)) + ref;
    n = Math.floor(n / 26) - 1;
  } while (n >= 0);
  return ref;
}

/**
 * A Date as the number Excel keeps: days since an imaginary 1899-12-30, which
 * is how the 1900-leap-year bug is absorbed. The time of day is the fraction.
 * Computed from the local components on purpose — the user picked "13 August",
 * not an instant, and shifting it by a timezone would move some rows a day.
 */
export function excelSerial(date) {
  const utc = Date.UTC(
    date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(),
    date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds(),
  );
  return (utc - Date.UTC(1899, 11, 30)) / 86400000;
}

/**
 * Excel refuses `[ ] : * ? / \`, an empty name, and anything past 31
 * characters. A caller passes an entity label, which is free text.
 */
export function sanitizeSheetName(name) {
  const cleaned = String(name || '').replace(/[[\]:*?/\\]/g, ' ').trim();
  return (cleaned || 'Sheet').slice(0, 31);
}

function _textCell(ref, text, style) {
  const s = style ? ` s="${style}"` : '';
  // A value with edge whitespace needs xml:space or a reader may trim it.
  const preserve = /^\s|\s$/.test(text) ? ' xml:space="preserve"' : '';
  return `<c r="${ref}"${s} t="inlineStr"><is><t${preserve}>${xmlEscape(text)}</t></is></c>`;
}

function _cellXml(ref, cell) {
  if (!cell) return '';
  const { type, value } = cell;

  if (value === null || value === undefined || value === '') return '';

  if (type === 'number' && Number.isFinite(value)) {
    return `<c r="${ref}"><v>${value}</v></c>`;
  }

  if ((type === 'date' || type === 'datetime') && value instanceof Date && !isNaN(value)) {
    const style = type === 'date' ? STYLE_DATE : STYLE_DATETIME;
    return `<c r="${ref}" s="${style}"><v>${excelSerial(value)}</v></c>`;
  }

  return _textCell(ref, String(value), STYLE_DEFAULT);
}

function _sheetXml(headers, rows) {
  const parts = [];

  const headerCells = headers
    .map((h, i) => _textCell(`${columnRef(i)}1`, String(h ?? ''), STYLE_HEADER))
    .join('');
  parts.push(`<row r="1">${headerCells}</row>`);

  rows.forEach((row, r) => {
    const rowNum = r + 2;
    const cells = row.map((cell, c) => _cellXml(`${columnRef(c)}${rowNum}`, cell)).join('');
    parts.push(`<row r="${rowNum}">${cells}</row>`);
  });

  // A width per column so the first thing the reader sees is not ####. Sized
  // from the header and a sample of the body — reading every row of a large
  // export to measure it would cost more than it is worth.
  const sample = rows.slice(0, 200);
  const cols = headers.map((h, i) => {
    const widest = sample.reduce((max, row) => {
      const cell = row[i];
      const len = cell ? String(cell.text ?? cell.value ?? '').length : 0;
      return Math.max(max, len);
    }, String(h ?? '').length);
    return `<col min="${i + 1}" max="${i + 1}" width="${Math.min(Math.max(widest + 2, 8), 60)}" customWidth="1"/>`;
  }).join('');

  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
    + `<worksheet xmlns="${_NS_MAIN}">`
    + (cols ? `<cols>${cols}</cols>` : '')
    + `<sheetData>${parts.join('')}</sheetData>`
    + `</worksheet>`;
}

const _STYLES_XML = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
  + `<styleSheet xmlns="${_NS_MAIN}">`
  + `<numFmts count="2">`
  + `<numFmt numFmtId="164" formatCode="yyyy\\-mm\\-dd"/>`
  + `<numFmt numFmtId="165" formatCode="yyyy\\-mm\\-dd\\ hh:mm"/>`
  + `</numFmts>`
  + `<fonts count="2">`
  + `<font><sz val="11"/><name val="Calibri"/></font>`
  + `<font><b/><sz val="11"/><name val="Calibri"/></font>`
  + `</fonts>`
  // Excel requires at least these two fills, in this order, present or not.
  + `<fills count="2">`
  + `<fill><patternFill patternType="none"/></fill>`
  + `<fill><patternFill patternType="gray125"/></fill>`
  + `</fills>`
  + `<borders count="1"><border/></borders>`
  + `<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>`
  + `<cellXfs count="4">`
  + `<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>`
  + `<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>`
  + `<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>`
  + `<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>`
  + `</cellXfs>`
  + `<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>`
  + `</styleSheet>`;

const _CONTENT_TYPES = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
  + `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">`
  + `<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>`
  + `<Default Extension="xml" ContentType="application/xml"/>`
  + `<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>`
  + `<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`
  + `<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>`
  + `</Types>`;

const _ROOT_RELS = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
  + `<Relationships xmlns="${_NS_REL_PKG}">`
  + `<Relationship Id="rId1" Type="${_NS_REL_DOC}/officeDocument" Target="xl/workbook.xml"/>`
  + `</Relationships>`;

const _WORKBOOK_RELS = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
  + `<Relationships xmlns="${_NS_REL_PKG}">`
  + `<Relationship Id="rId1" Type="${_NS_REL_DOC}/worksheet" Target="worksheets/sheet1.xml"/>`
  + `<Relationship Id="rId2" Type="${_NS_REL_DOC}/styles" Target="styles.xml"/>`
  + `</Relationships>`;

/**
 * Build the workbook.
 *
 * @param {object} spec
 * @param {string} spec.sheetName  the entity label; sanitised for Excel
 * @param {string[]} spec.headers  column labels
 * @param {Array<Array<{type,value,text}>>} spec.rows  cells as `cellValue` returns them
 * @returns {Promise<Uint8Array>} the .xlsx bytes
 */
export async function buildXlsx({ sheetName, headers = [], rows = [] }) {
  const zip = new JSZip();
  const name = sanitizeSheetName(sheetName);

  zip.file('[Content_Types].xml', _CONTENT_TYPES);
  zip.folder('_rels').file('.rels', _ROOT_RELS);
  zip.folder('xl').file(
    'workbook.xml',
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
    + `<workbook xmlns="${_NS_MAIN}" xmlns:r="${_NS_REL_DOC}">`
    + `<sheets><sheet name="${xmlEscape(name)}" sheetId="1" r:id="rId1"/></sheets>`
    + `</workbook>`,
  );
  zip.folder('xl').folder('_rels').file('workbook.xml.rels', _WORKBOOK_RELS);
  zip.folder('xl').file('styles.xml', _STYLES_XML);
  zip.folder('xl').folder('worksheets').file('sheet1.xml', _sheetXml(headers, rows));

  return zip.generateAsync({
    type: 'uint8array',
    compression: 'DEFLATE',
    compressionOptions: { level: 6 },
  });
}

export const XLSX_MIME =
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

export default buildXlsx;
