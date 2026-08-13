// -----------------------------------------------------------------------------
// useTableExport — the rows an export writes.
//
// The rows are fetched, not scraped off the screen, and they are fetched by
// RE-RUNNING the caller's own list request: same filters, same search, same
// sort, same role. That is the whole safety argument for exporting in the
// browser — field masking, row visibility, owner scope and the read-role floor
// were all applied by the server on the way out, once, and an export that can
// only ever see what the list served cannot leak past any of them.
//
// It also means this hook knows nothing about sandboxes, tokens or entities. It
// is handed a `fetchPage(page)` and it loops. `common/` never imports a feature
// module, and this is where that rule lands.
// -----------------------------------------------------------------------------

import { useCallback, useState } from 'react';
import { exportData, buildRows, EXPORT_MAX_ROWS } from '../tools/export';

// What one request asks for. Matches the backend's clamp
// (`EXPORT_MAX_PAGE_SIZE`), so the common case is one round trip and a large
// table is a handful.
export const EXPORT_PAGE_SIZE = 500;

// A table can always be walked in this many requests or it is refused. Without
// it, a `pages` that never decrements — a filter the server ignores, a count
// that disagrees with the page — is an infinite loop in someone's browser.
const MAX_REQUESTS = Math.ceil(EXPORT_MAX_ROWS / EXPORT_PAGE_SIZE) + 2;

/**
 * @param {object} opts
 * @param {function} opts.fetchPage  `(page, pageSize) => Promise<{items, pages, count}>`
 * @param {function} opts.getSpec    `(records) => spec for exportData` — the
 *                                   caller owns columns, labels, filename and
 *                                   the header metadata, because only it knows
 *                                   what it is showing
 * @returns {{run, busy, progress}}  `run(format)` resolves `{ok, reason}`
 */
export function useTableExport({ fetchPage, getSpec }) {
  const [busy, setBusy] = useState(false);
  // 0..1, or null when there is nothing to report yet. Only meaningful once the
  // first page has told us how many there are.
  const [progress, setProgress] = useState(null);

  const collect = useCallback(async () => {
    const records = [];
    let page = 1;
    let pages = 1;

    for (let request = 0; request < MAX_REQUESTS; request += 1) {
      // eslint-disable-next-line no-await-in-loop
      const body = await fetchPage(page, EXPORT_PAGE_SIZE);
      const items = body?.items || [];
      records.push(...items);

      pages = Math.max(1, Number(body?.pages) || 1);
      setProgress(Math.min(1, page / pages));

      if (records.length > EXPORT_MAX_ROWS) {
        // Stop fetching the moment the answer is "too many": there is no point
        // paying for the rest of a table we are about to refuse.
        return { tooMany: true, records };
      }
      if (page >= pages || items.length === 0) return { tooMany: false, records };
      page += 1;
    }

    // Ran out of requests with pages still to go. Refusing is the only honest
    // outcome — a file built from what we happened to collect looks complete.
    return { tooMany: true, records };
  }, [fetchPage]);

  const run = useCallback(async (format) => {
    if (busy) return { ok: false, reason: 'export-busy' };
    setBusy(true);
    setProgress(null);
    try {
      const { tooMany, records } = await collect();
      if (tooMany) {
        return { ok: false, reason: 'export-too-many-rows', limit: EXPORT_MAX_ROWS };
      }
      const spec = getSpec(records) || {};
      const rows = spec.rows || buildRows(records, spec.columns || [], spec);
      return await exportData({ ...spec, rows, format });
    } catch (err) {
      console.warn('[export] could not collect rows', err);  // eslint-disable-line no-console
      return { ok: false, reason: 'export-fetch-failed' };
    } finally {
      setBusy(false);
      setProgress(null);
    }
  }, [busy, collect, getSpec]);

  return { run, busy, progress };
}

export default useTableExport;
