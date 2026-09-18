// -----------------------------------------------------------------------------
// runImport — the rows, written one at a time through the caller's own create.
//
// This is export's argument, inverted, and it is the whole design of the
// runtime half:
//
//   *The export loops the same LIST request the table is showing, so field
//   masking, row visibility, owner scope, persona identity and the read floor
//   apply with nothing re-implemented — and it can never write a file holding a
//   row the list would not have shown.*
//
// So the import posts through the same CREATE request the form posts through.
// The write role, the model validation, the required check, the numeric / geo /
// tag-list normalisation on the write boundary, the on-create behaviours and
// the computed fields all apply with nothing re-implemented — and it can never
// write a row the form could not have written. A bulk endpoint would be a
// second write path past all of them, in the module whose three worst bugs
// were all a writer that went round the first one.
//
// The cost is one request per row, which is the honest price of that guarantee
// and is why `IMPORT_MAX_ROWS` exists.
//
// It never throws. Every row's outcome is recorded and the caller is handed a
// report; a run that fails halfway is a run that says which rows landed.
// -----------------------------------------------------------------------------

import { coerceCell } from './coerce';

/**
 * Build one create payload from one file row.
 *
 * Absent values are LEFT OUT rather than sent as `''` or `0`: blank is unknown,
 * and a required field that is blank in the file has to be refused by the
 * server rather than filled in here with something that looks like an answer.
 */
export function buildPayload(row, mapping, fieldsByName) {
  const payload = {};
  Object.entries(mapping || {}).forEach(([columnIndex, fieldName]) => {
    if (!fieldName) return;
    const field = fieldsByName[fieldName] || { name: fieldName };
    const value = coerceCell(row[Number(columnIndex)], field);
    if (value === undefined) return;
    if (Array.isArray(value) && value.length === 0) return;
    payload[fieldName] = value;
  });
  return payload;
}

/**
 * The reason one row was refused, as a sentence.
 *
 * A create endpoint answers `{detail: [{field: ['key']}]}` on a validation
 * failure and `{detail: 'code'}` on an envelope one, and both reach the report
 * — the owner is looking for *which column is wrong in my file*, so the field
 * name is kept and never flattened into "row 14 failed".
 */
export function describeFailure(error, t) {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);
  const detail = error?.response?.data?.detail ?? error?.detail ?? error;
  if (typeof detail === 'string') return tval(detail, detail);
  if (Array.isArray(detail)) {
    const parts = [];
    detail.forEach((entry) => {
      if (typeof entry === 'string') { parts.push(tval(entry, entry)); return; }
      Object.entries(entry || {}).forEach(([field, messages]) => {
        (Array.isArray(messages) ? messages : [messages]).forEach((message) => {
          parts.push(`${field}: ${tval(message, message)}`);
        });
      });
    });
    if (parts.length) return parts.join(' · ');
  }
  return tval('import-row-failed', 'This row could not be saved');
}

/**
 * Write every row, in order, through `createRecord`.
 *
 * @param {object} options
 *   `rows`          the file's data rows
 *   `mapping`       `{columnIndex: fieldName}`
 *   `fields`        the entity's fields (`{name, field_type, choices, options}`)
 *   `createRecord`  `async (payload) => any` — the caller's own create call
 *   `onProgress`    `({done, total, created, failed}) => void`
 *   `stopAfter`     give up after this many consecutive failures
 *   `t`             translator, for the failure sentences
 *
 * @returns `{created, failed, rows, stopped}` where `failed` is
 *   `[{row, line, reason}]` — `line` being the line number IN THE FILE, header
 *   included, because that is the number the owner's spreadsheet shows.
 */
export async function runImport({
  rows = [],
  mapping = {},
  fields = [],
  createRecord,
  onProgress,
  stopAfter = 25,
  t,
} = {}) {
  const fieldsByName = {};
  (fields || []).forEach((f) => { fieldsByName[f.name] = f; });

  const failed = [];
  let created = 0;
  let consecutive = 0;
  let stopped = false;

  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index] || [];
    // A row that maps to nothing at all is a blank line in the middle of a
    // file, not a failure: sending it would create an empty record.
    const payload = buildPayload(row, mapping, fieldsByName);
    if (!Object.keys(payload).length) continue;

    try {
      // eslint-disable-next-line no-await-in-loop
      await createRecord(payload);
      created += 1;
      consecutive = 0;
    } catch (error) {
      failed.push({
        row: index,
        line: index + 2,        // +1 for the header, +1 for counting from one
        reason: describeFailure(error, t),
      });
      consecutive += 1;
      // A whole file failing the same way — the wrong column mapped to a
      // required field, an expired session — is one mistake repeated, and
      // running it out to five thousand requests neither helps the owner nor
      // the server.
      if (stopAfter && consecutive >= stopAfter) { stopped = true; break; }
    }
    if (onProgress) {
      onProgress({ done: index + 1, total: rows.length, created, failed: failed.length });
    }
  }

  return { created, failed, rows: rows.length, stopped };
}

export default runImport;
