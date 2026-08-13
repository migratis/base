// -----------------------------------------------------------------------------
// csv — the same table as plain text.
//
// It falls out of the column model for nothing, and it is the format that opens
// everywhere, so it is offered rather than kept as an implementation detail.
//
// Two decisions worth stating. It writes the cell's TEXT, not its typed value:
// a CSV has no types, so the honest thing to put in it is the reading the user
// saw. And it starts with a UTF-8 BOM, because Excel on Windows still reads a
// BOM-less CSV as the local 8-bit codepage and turns every accented character
// in a French or Romanian app into mojibake.
// -----------------------------------------------------------------------------

const _BOM = '﻿';

// Excel picks the separator from the locale, and there is no in-file way to
// declare it other than the `sep=` line, which some readers show as data. A
// comma is the portable default; the caller may ask for a semicolon.
export function csvEscape(text, separator = ',') {
  const s = String(text ?? '');
  const mustQuote = s.includes(separator) || s.includes('"')
    || s.includes('\n') || s.includes('\r');
  return mustQuote ? `"${s.replace(/"/g, '""')}"` : s;
}

/**
 * @param {object} spec
 * @param {string[]} spec.headers
 * @param {Array<Array<{type,value,text}>>} spec.rows  cells as `cellValue` returns them
 * @param {string} spec.separator
 * @returns {string} the file's contents
 */
export function buildCsv({ headers = [], rows = [], separator = ',' }) {
  const lines = [headers.map((h) => csvEscape(h, separator)).join(separator)];
  for (const row of rows) {
    lines.push(row.map((cell) => csvEscape(cell?.text ?? '', separator)).join(separator));
  }
  // CRLF, which is what RFC 4180 says and what Excel is happiest with.
  return _BOM + lines.join('\r\n') + '\r\n';
}

export const CSV_MIME = 'text/csv;charset=utf-8';

export default buildCsv;
