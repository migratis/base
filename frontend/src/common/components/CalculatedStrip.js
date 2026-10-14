/**
 * The strip on a calculated table's tab (SCOPE_calculated_tables.md §6.6).
 *
 *   Calculated table · Projection · Calculated 14/10/2026 10:32 · 36 rows ·
 *   Inputs changed since — Recalculate
 *
 * A calculated table is read-only to everything but its calculation, so the
 * tab has no New / Edit / Delete; this strip is what it has instead — when it
 * last ran, how many rows, whether an input moved since, and how to run it
 * again. Staleness is the server's reading (it compares the inputs' own
 * timestamps with the last successful run); a write that bypasses every
 * pipeline is not seen, so this says *as of the last run* and nothing more.
 *
 * An anchored table (one set per Projection, per Season) is recalculated from
 * the anchor's own button — the strip points there rather than guessing which
 * anchor to run. Lives in `common/` because every generated application
 * renders the same strip on the same tab (P5).
 */
import React from 'react';

const CalculatedStrip = ({ derived, t, onRecalculate, busy = false }) => {
  if (!derived) return null;
  const last = derived.last_run;
  const when = last?.at ? new Date(last.at).toLocaleString() : '';

  return (
    <div className="calculated-strip" role="status">
      <span className="calculated-strip-title">
        {t('calculated-table', 'Calculated table')}
        {derived.label ? ` · ${derived.label}` : ''}
      </span>
      {!last && (
        <span className="calculated-strip-item">
          {t('calculated-never', 'Not calculated yet')}
        </span>
      )}
      {last && last.status === 'ok' && (
        <>
          <span className="calculated-strip-item">
            {t('calculated-at', { when, defaultValue: 'Calculated {{when}}' })}
          </span>
          <span className="calculated-strip-item">
            {t('calculated-rows', { count: last.rows, defaultValue: '{{count}} rows' })}
          </span>
        </>
      )}
      {last && last.status !== 'ok' && (
        <span className="calculated-strip-item calculated-strip-refused">
          {t('calculated-refused', {
            error: last.error || last.error_code,
            defaultValue: 'Last run refused: {{error}}',
          })}
        </span>
      )}
      {derived.stale && (
        <span className="badge bg-warning text-dark calculated-strip-stale">
          {t('calculated-stale', 'Inputs changed since')}
        </span>
      )}
      {derived.anchored ? (
        <span className="calculated-strip-hint">
          {t('calculated-from-anchor', {
            anchor: derived.anchor_entity,
            defaultValue: 'Calculated for each {{anchor}} — use its button to recalculate',
          })}
        </span>
      ) : onRecalculate && (
        <button
          type="button"
          className="btn btn-sm btn-outline-primary calculated-strip-run"
          onClick={() => onRecalculate(derived.derivation_id)}
          disabled={busy}
        >
          {t('calculated-recalculate', 'Recalculate')}
        </button>
      )}
    </div>
  );
};

export default CalculatedStrip;
