import api from '../../common/tools/axios';

/**
 * Running a lookup — the runtime half of external data sources
 * (SCOPE_external_data_sources.md@d2de531 §4).
 *
 * Two transports, one shape. The design sandbox asks
 * `POST /sandbox/{token}/{entity}/lookup`; a generated application asks
 * `POST /datasource/{slug}/lookup`; both answer
 * `{candidates: [{label, id, values}]}` and **neither writes anything**. The
 * control that renders them therefore does not know which world it is in — the
 * host hands it one of these.
 *
 * §8.4 — three outcomes, told apart because the caller does something different
 * with each, and **a quota stop is never an empty candidate list**:
 *
 *   `datasource-unavailable`      keep what the user typed, badge the button
 *   `datasource-refused`          the owner's key; say so, with the status
 *   `datasource-quota-exhausted`  out of lookups for today
 *   ok + zero candidates          the source answered and has nothing. Real.
 *
 * `common/tools/axios` resolves on an error response, so **the status decides**,
 * never the absence of a field: a 503 body and a 504 of nginx HTML both arrive
 * with no `candidates`, and reading only the field would render every transport
 * failure as "nothing found" — which is the mistake `refreshOutcome` exists to
 * stop making one module over.
 */

export const UNAVAILABLE     = 'datasource-unavailable';
export const REFUSED         = 'datasource-refused';
export const QUOTA_EXHAUSTED = 'datasource-quota-exhausted';
export const RATE_LIMITED    = 'datasource-rate-limited';

const NAMED = new Set([UNAVAILABLE, REFUSED, QUOTA_EXHAUSTED, RATE_LIMITED]);

export function readOutcome(response) {
  const status = response?.status;
  if (status >= 200 && status < 300) {
    const candidates = response?.data?.candidates;
    return {
      ok: true,
      candidates: Array.isArray(candidates) ? candidates : [],
      needsDetail: Boolean(response?.data?.needs_detail),
      values: response?.data?.values,
      label: response?.data?.label,
      id: response?.data?.id,
    };
  }
  const detail = response?.data?.detail;
  // A name we know, or the honest default. The list of envelopes the frontend
  // knows by name has never been the list the backend can send.
  const key = NAMED.has(detail) ? detail : UNAVAILABLE;
  return { ok: false, key, sourceStatus: response?.data?.source_status || null,
           candidates: [] };
}

/** The design sandbox's transport. */
export function sandboxLookup(token, entityName) {
  return {
    search: async (sourceId, q) => readOutcome(
      await api.post(`/generator/sandbox/${token}/${entityName}/lookup`,
                     { source: sourceId, q })),
    detail: async (sourceId, id) => readOutcome(
      await api.post(`/generator/sandbox/${token}/${entityName}/lookup-detail`,
                     { source: sourceId, id })),
  };
}

/** A generated application's transport — the same shape, its own endpoint. */
export function appLookup(entityName) {
  return {
    search: async (sourceId, q) => readOutcome(
      await api.post(`/datasource/${sourceId}/lookup`, { entity: entityName, q })),
    detail: async (sourceId, id) => readOutcome(
      await api.post(`/datasource/${sourceId}/lookup-detail`,
                     { entity: entityName, id })),
  };
}
