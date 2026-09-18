// -----------------------------------------------------------------------------
// csv — a delimited text file, read as a header row and rows.
//
// The mirror of `../export/csv.js`, and written here for the same reason that
// one was: what we need is a flat sheet, and a parser dependency for a flat
// sheet is a dependency in two repos and in every generated application.
//
// Two things a hand-rolled reader has to get right, because both are silent
// when wrong:
//
// **The delimiter.** A French or German Excel writes `;` by default — its CSV
// is delimited by whatever the locale's list separator is — so a parser that
// assumes `,` reads such a file as ONE column holding the whole line, which
// then proposes one field called `name;year;kind`. It is sniffed, over the
// header line only, counting outside quotes.
//
// **Quoting.** A quoted field may hold the delimiter, a line break and a
// doubled quote. Splitting on the delimiter is right until the first address
// or synopsis, at which point every row after it is shifted by one column and
// the file still parses.
// -----------------------------------------------------------------------------

//: In the order they are preferred when the counts tie. `,` first because it is
//: the format's name; `\t` last because a tab inside a quoted cell is common.
export const DELIMITERS = [',', ';', '\t', '|'];

/**
 * The delimiter a line is most likely written with.
 *
 * Counted outside quotes: `"Paris, France";1` is one semicolon and not one
 * comma, and counting inside the quotes would answer `,` for a file that has
 * exactly one comma in it and it is part of a value.
 */
export function sniffDelimiter(line) {
  const counts = new Map(DELIMITERS.map((d) => [d, 0]));
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      // A doubled quote inside a quoted field is an escaped quote, not the end.
      if (inQuotes && line[i + 1] === '"') { i += 1; continue; }
      inQuotes = !inQuotes;
      continue;
    }
    if (!inQuotes && counts.has(ch)) counts.set(ch, counts.get(ch) + 1);
  }
  let best = DELIMITERS[0];
  let bestCount = 0;
  DELIMITERS.forEach((d) => {
    if (counts.get(d) > bestCount) { best = d; bestCount = counts.get(d); }
  });
  return best;
}

/**
 * Parse delimited text.
 *
 * @param {string} text        the file's contents
 * @param {object} options     `{delimiter}` to override the sniff
 * @returns {{columns: string[], rows: string[][], delimiter: string}}
 *
 * The first row is the header. A file whose first row is data produces columns
 * named after its first record, which is wrong in a way the owner can SEE in
 * the mapping step — as against a "first row is data" toggle nobody would find
 * before being surprised by it.
 */
export function parseCsv(text, options = {}) {
  // A BOM is invisible and would otherwise ride into the first header, whose
  // field name then folds to `c_...` and matches nothing.
  const body = String(text || '').replace(/^﻿/, '');
  const firstLine = body.split(/\r?\n/, 1)[0] || '';
  const delimiter = options.delimiter || sniffDelimiter(firstLine);

  const matrix = [];
  let row = [];
  let cell = '';
  let inQuotes = false;
  let cellWasQuoted = false;

  const endCell = () => {
    row.push(cell);
    cell = '';
    cellWasQuoted = false;
  };
  const endRow = () => {
    endCell();
    matrix.push(row);
    row = [];
  };

  for (let i = 0; i < body.length; i += 1) {
    const ch = body[i];
    if (inQuotes) {
      if (ch === '"') {
        if (body[i + 1] === '"') { cell += '"'; i += 1; continue; }
        inQuotes = false;
        continue;
      }
      cell += ch;
      continue;
    }
    if (ch === '"' && cell === '') { inQuotes = true; cellWasQuoted = true; continue; }
    if (ch === delimiter) { endCell(); continue; }
    if (ch === '\r') continue;          // CRLF — the \n does the work
    if (ch === '\n') { endRow(); continue; }
    cell += ch;
  }
  // A file that does not end in a newline still has a last row; one that does
  // must not gain an empty one.
  if (cell !== '' || cellWasQuoted || row.length) endRow();

  // Trailing blank lines are the normal state of a file somebody edited.
  while (matrix.length && matrix[matrix.length - 1].every((c) => c.trim() === '')) {
    matrix.pop();
  }

  const [header = [], ...rest] = matrix;
  return {
    columns: header.map((c) => String(c).trim()),
    rows: rest,
    delimiter,
  };
}
