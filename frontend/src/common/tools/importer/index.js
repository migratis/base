// -----------------------------------------------------------------------------
// parseTabularFile — the one door in.
//
// The mirror of `../export/index.js`, and the reason the whole importer lives
// under `common/`: the sandbox reads a file, a generated application reads a
// file, and they read it with the same code — so a spreadsheet that imports in
// the preview imports in the shipped application, structurally rather than by
// somebody keeping two readers in agreement.
//
// It never throws into a render. A caller is an `onChange` on a file input, and
// a rejected promise there is an unhandled rejection with nothing on screen —
// so every failure resolves as `{ok: false, reason}` and the caller says it.
// -----------------------------------------------------------------------------

import { parseCsv } from './csv';
import { parseXlsx } from './xlsx';
import { IMPORT_MAX_ROWS, INFERENCE_SAMPLE_ROWS } from './constants';

export { parseCsv, sniffDelimiter, DELIMITERS } from './csv';
export { parseXlsx } from './xlsx';
export {
  coerceCell, isBlank, numberText, mappableFields, guessMapping, UNMAPPABLE_TYPES,
} from './coerce';
export { runImport } from './runImport';
export { importTargets } from './targets';
export {
  IMPORT_MAX_ROWS, INFERENCE_SAMPLE_ROWS, IMPORT_ACCEPT, LIST_JOIN,
} from './constants';

const _XLSX_EXT = /\.xlsx$/i;
const _TEXT_EXT = /\.(csv|tsv|txt)$/i;

function readAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error || new Error('read-failed'));
    // UTF-8 is the only encoding guessed at. A Latin-1 export shows its
    // mojibake in the mapping table's sample values, where the owner can see it
    // and re-export — as against a silent transliteration of somebody's name.
    reader.readAsText(file, 'utf-8');
  });
}

function readAsArrayBuffer(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error || new Error('read-failed'));
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Read a picked file into columns and rows.
 *
 * @param {File} file
 * @returns {Promise<{ok, columns, rows, sheetName, filename, reason}>}
 *
 * `reason` is one of `import-no-file`, `import-format-unknown`,
 * `import-read-failed`, `import-empty-file`, `import-too-many-rows` — each an
 * i18n key, seeded, so the caller toasts a sentence rather than a code.
 */
export async function parseTabularFile(file) {
  if (!file) return { ok: false, reason: 'import-no-file' };
  const name = file.name || '';

  let parsed;
  try {
    if (_XLSX_EXT.test(name)) {
      parsed = await parseXlsx(await readAsArrayBuffer(file));
    } else if (_TEXT_EXT.test(name)) {
      parsed = parseCsv(await readAsText(file));
    } else {
      return { ok: false, reason: 'import-format-unknown', filename: name };
    }
  } catch (e) {
    // A corrupt zip, an unreadable encoding, a file the user moved mid-read.
    // One reason, because to the reader they are one fact: this file did not
    // open.
    return { ok: false, reason: 'import-read-failed', filename: name };
  }

  const columns = parsed.columns || [];
  const rows = parsed.rows || [];
  if (!columns.length) {
    return { ok: false, reason: 'import-empty-file', filename: name };
  }
  if (rows.length > IMPORT_MAX_ROWS) {
    // Refused whole rather than truncated — a file that silently imported its
    // first five thousand rows looks exactly like one that imported.
    return {
      ok: false, reason: 'import-too-many-rows', filename: name,
      rows: rows.length, limit: IMPORT_MAX_ROWS,
    };
  }

  return {
    ok: true,
    filename: name,
    sheetName: parsed.sheetName || '',
    delimiter: parsed.delimiter || '',
    columns,
    rows,
  };
}

/** The first `INFERENCE_SAMPLE_ROWS` rows, as the proposal endpoint takes them. */
export function inferenceSample(rows) {
  return (rows || []).slice(0, INFERENCE_SAMPLE_ROWS);
}

export default parseTabularFile;
