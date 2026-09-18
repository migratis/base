// -----------------------------------------------------------------------------
// xlsx — a minimal .xlsx reader.
//
// The mirror of `../export/xlsx.js`: an .xlsx is a zip of small XML parts, and
// `jszip` is already a declared dependency in both repos. npm's `xlsx` is a
// stale build carrying advisories and `exceljs` is about a megabyte, both of
// which would then ship in every generated application.
//
// Reading is harder than writing in exactly two places, and both are silent
// when wrong.
//
// **A string cell usually holds a NUMBER.** `t="s"` means the `<v>` is an index
// into `sharedStrings.xml`, so a reader that takes `<v>` at face value answers
// `0`, `1`, `2` for the first three distinct strings in the file — a column of
// small integers where the titles were.
//
// **A date is a number too.** Excel stores `2026-01-04` as `46026` and the only
// thing that makes it a date is the *format* attached through the cell's style.
// A reader that ignores styles proposes an `integer` column of five-digit
// numbers, which is exactly the shape that gets imported and then noticed a
// week later.
//
// Everything comes back as TEXT, the shape `csv.js` answers, so the inference
// and the mapping see one thing rather than two. A date cell comes back as its
// ISO date because that is the only lossless text for it.
// -----------------------------------------------------------------------------

import JSZip from 'jszip';

// Excel's day 0. 1899-12-30 rather than 1899-12-31 because the format carries
// a deliberate bug — it believes 1900 was a leap year — and the offset absorbs
// it for every date after 1900-03-01, which is every date anybody imports.
const _EPOCH_MS = Date.UTC(1899, 11, 30);
const _DAY_MS = 24 * 60 * 60 * 1000;

// The built-in number formats that mean a date or a time. Fixed by the file
// format, so they are listed rather than sniffed.
const _BUILTIN_DATE_FORMATS = new Set([
  14, 15, 16, 17, 18, 19, 20, 21, 22, 45, 46, 47,
]);

// A custom format code that mentions a date or time component. Quoted literals
// and the colour/condition brackets are removed first: `[Red]0.00" days"` is
// not a date, and both of its `d`s would say it was.
function looksLikeDate(formatCode) {
  const bare = String(formatCode || '')
    .replace(/"[^"]*"/g, '')
    .replace(/\[[^\]]*\]/g, '')
    .replace(/\\./g, '');
  return /[ymdhs]/i.test(bare) && !/^general$/i.test(bare.trim());
}

function parseXml(text) {
  return new DOMParser().parseFromString(text, 'application/xml');
}

/** `AB12` → 27. Anything unreadable answers -1 so the caller can fall back to
 *  document order rather than putting a cell in column A. */
export function columnIndex(ref) {
  const letters = String(ref || '').match(/^[A-Z]+/i);
  if (!letters) return -1;
  return letters[0].toUpperCase().split('').reduce(
    (acc, ch) => acc * 26 + (ch.charCodeAt(0) - 64), 0) - 1;
}

/** An Excel day serial as an ISO date, or an ISO datetime when it carries a
 *  time of day. */
export function serialToIso(serial) {
  const ms = _EPOCH_MS + Math.round(Number(serial) * _DAY_MS);
  const date = new Date(ms);
  if (Number.isNaN(date.getTime())) return String(serial);
  const iso = date.toISOString();
  // A whole-day serial is a date. Keeping the `T00:00:00.000Z` would make every
  // date column read as `datetime`, and a timezone the file never mentioned.
  const fractional = Math.abs(Number(serial) % 1) > 1e-9;
  return fractional ? iso.slice(0, 19) : iso.slice(0, 10);
}

// A double, as the shortest text that means the same number. Excel stores
// binary doubles, so a cell a human typed as 197.8 can come back as
// 197.80000000000001 and land in the proposal as that.
function numberText(raw) {
  const n = Number(raw);
  if (!Number.isFinite(n)) return String(raw);
  return String(Number(n.toPrecision(15)));
}

function sharedStrings(doc) {
  if (!doc) return [];
  return Array.from(doc.getElementsByTagName('si')).map((si) => {
    // `<si>` is either one `<t>` or a run of them (`<r><t>`), which is what a
    // cell with mixed formatting looks like. Both are the same string.
    const parts = Array.from(si.getElementsByTagName('t')).map((t) => t.textContent);
    return parts.join('');
  });
}

function dateStyles(doc) {
  const isDate = new Set();
  if (!doc) return isDate;
  const custom = new Map();
  Array.from(doc.getElementsByTagName('numFmt')).forEach((fmt) => {
    custom.set(Number(fmt.getAttribute('numFmtId')), fmt.getAttribute('formatCode'));
  });
  const cellXfs = doc.getElementsByTagName('cellXfs')[0];
  if (!cellXfs) return isDate;
  Array.from(cellXfs.getElementsByTagName('xf')).forEach((xf, index) => {
    const id = Number(xf.getAttribute('numFmtId') || 0);
    if (_BUILTIN_DATE_FORMATS.has(id) || looksLikeDate(custom.get(id))) {
      isDate.add(index);
    }
  });
  return isDate;
}

function cellText(cell, strings, dateStyleIndexes) {
  const type = cell.getAttribute('t');
  if (type === 'inlineStr') {
    return Array.from(cell.getElementsByTagName('t'))
      .map((t) => t.textContent).join('');
  }
  const v = cell.getElementsByTagName('v')[0];
  if (!v) return '';
  const raw = v.textContent;
  if (type === 's') return strings[Number(raw)] ?? '';
  if (type === 'str') return raw;                       // a formula's string result
  if (type === 'b') return raw === '1' ? 'true' : 'false';
  if (type === 'e') return '';                          // #N/A, #REF! — nothing
  const style = Number(cell.getAttribute('s') || -1);
  if (dateStyleIndexes.has(style)) return serialToIso(raw);
  return numberText(raw);
}

async function readPart(zip, path) {
  const file = zip.file(path);
  return file ? parseXml(await file.async('string')) : null;
}

/**
 * Read the first worksheet of an .xlsx.
 *
 * @param {ArrayBuffer} buffer
 * @returns {Promise<{columns: string[], rows: string[][], sheetName: string}>}
 *
 * The FIRST sheet, deliberately, and its name travels back so the modal can
 * say which one it read. Offering a sheet picker before the owner has seen a
 * single value is a question asked too early; a workbook whose data is on the
 * second sheet shows a header row the owner will not recognise, which is the
 * same information arriving in the right order.
 */
export async function parseXlsx(buffer) {
  const zip = await JSZip.loadAsync(buffer);

  const workbook = await readPart(zip, 'xl/workbook.xml');
  const rels = await readPart(zip, 'xl/_rels/workbook.xml.rels');
  const strings = sharedStrings(await readPart(zip, 'xl/sharedStrings.xml'));
  const dateStyleIndexes = dateStyles(await readPart(zip, 'xl/styles.xml'));

  const sheetEl = workbook && workbook.getElementsByTagName('sheet')[0];
  const sheetName = sheetEl ? (sheetEl.getAttribute('name') || '') : '';

  // The sheet's path comes from the relationship its r:id names. Assuming
  // `xl/worksheets/sheet1.xml` is right for most writers and wrong for enough
  // of them — Google Sheets and LibreOffice both emit other names.
  let target = 'xl/worksheets/sheet1.xml';
  const relId = sheetEl && (sheetEl.getAttribute('r:id') || sheetEl.getAttribute('id'));
  if (rels && relId) {
    const match = Array.from(rels.getElementsByTagName('Relationship'))
      .find((rel) => rel.getAttribute('Id') === relId);
    if (match) {
      const raw = match.getAttribute('Target') || '';
      target = raw.startsWith('/') ? raw.slice(1)
        : (raw.startsWith('xl/') ? raw : `xl/${raw}`);
    }
  }

  const sheet = await readPart(zip, target);
  if (!sheet) return { columns: [], rows: [], sheetName };

  const matrix = [];
  Array.from(sheet.getElementsByTagName('row')).forEach((rowEl) => {
    const cells = Array.from(rowEl.getElementsByTagName('c'));
    const values = [];
    cells.forEach((cell, position) => {
      // A row omits its empty cells entirely, so the `r` reference is what
      // keeps a column aligned. Without it, one blank cell shifts every value
      // after it one column to the left, for that row only.
      const index = columnIndex(cell.getAttribute('r'));
      const at = index >= 0 ? index : position;
      while (values.length < at) values.push('');
      values[at] = cellText(cell, strings, dateStyleIndexes);
    });
    matrix.push(values);
  });

  while (matrix.length && matrix[matrix.length - 1].every((c) => String(c).trim() === '')) {
    matrix.pop();
  }

  const [header = [], ...rest] = matrix;
  return {
    columns: header.map((c) => String(c == null ? '' : c).trim()),
    rows: rest,
    sheetName,
  };
}
