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
 * The reason a write was refused, as a sentence.
 *
 * There are **three** shapes on the wire and this reads all of them, because
 * the owner is looking for *which column is wrong in my file* and a report
 * that flattens that into "row 14 failed" sends them back to the spreadsheet
 * with nothing to look for:
 *
 *   1. `[{loc: ['form', field], msg, type}]` — `api.functions.formatErrors`,
 *      what every generator endpoint answers. Printing the raw entry gives
 *      `loc: form, name · msg: … · type: value_error.missing`, which is what
 *      the first version did.
 *   2. `{field: 'reason-code'}` — the sandbox's own field-level 422, the shape
 *      `sandbox/saveOutcome.js` was written for.
 *   3. `'code'` — a bare envelope (`forbidden-role`, …).
 *
 * A reason code is translated when the caller's vocabulary has it and shown
 * verbatim when it does not: a new backend code must still reach the user.
 */
export function describeFailure(error, t) {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);
  const detail = error?.response?.data?.detail ?? error?.detail ?? error;
  if (typeof detail === 'string') return tval(detail, detail);

  if (Array.isArray(detail)) {
    const parts = [];
    detail.forEach((entry) => {
      if (typeof entry === 'string') { parts.push(tval(entry, entry)); return; }
      if (entry && typeof entry === 'object' && 'msg' in entry) {
        // `loc` is ['form', <field>] or ['body', <schema>, <field>]; the last
        // segment is the one the owner can act on.
        const loc = Array.isArray(entry.loc) ? entry.loc[entry.loc.length - 1] : '';
        const msg = tval(entry.msg, entry.msg);
        parts.push(loc && loc !== 'form' ? `${loc}: ${msg}` : String(msg));
        return;
      }
      Object.entries(entry || {}).forEach(([field, messages]) => {
        (Array.isArray(messages) ? messages : [messages]).forEach((message) => {
          parts.push(`${field}: ${tval(message, message)}`);
        });
      });
    });
    if (parts.length) return parts.join(' · ');
  }

  if (detail && typeof detail === 'object') {
    const parts = Object.entries(detail).map(([field, reason]) => {
      const code = Array.isArray(reason) ? reason[0] : reason;
      return `${field}: ${tval(String(code), String(code))}`;
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
 *   `createRecord`  `async (payload) => any` — the caller's own create call.
 *                   It MUST REJECT when the row was refused. `common/tools/
 *                   axios` resolves on an error response, so a host that
 *                   forwards it raw would have every refusal counted as a
 *                   create; `acceptedOrThrow` from `./outcome` is what both
 *                   hosts wrap it in.
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
