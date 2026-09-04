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

/**
 * `url` with the claimed preview role on it, the way every other sandbox
 * request carries it (`sandbox.service`'s `_withViewAs`, which this module may
 * not import — `datasource` never reaches into `generator`, so the host hands
 * the claim down as a prop and this serialises it).
 *
 * The lookup's gate is the entity's own **write** role (D5), so a request that
 * states no claim is resolved as `public` and refused with `forbidden-role`
 * naming the very role the designer is previewing as. Both hops need it: the
 * PICK is a second request against the same gate.
 *
 * Persona '1' is the default and adds nothing, keeping the URL a legacy flow
 * would have produced.
 */
const _withViewAs = (url, viewAs, viewAsId) => {
  if (!viewAs) return url;
  const sep = url.includes('?') ? '&' : '?';
  let out = `${url}${sep}view_as=${encodeURIComponent(viewAs)}`;
  const persona = String(viewAsId == null ? '1' : viewAsId);
  if (persona !== '1') out += `&view_as_id=${encodeURIComponent(persona)}`;
  return out;
};

/**
 * The design sandbox's transport.
 *
 * `viewAs` is the *claimed* preview role and belongs to the sandbox alone —
 * `appLookup` below deliberately has no counterpart, because a generated
 * application authenticates its user and a claim there would be an escalation.
 */
export function sandboxLookup(token, entityName, viewAs = null, viewAsId = '1') {
  const url = (suffix) => _withViewAs(
    `/generator/sandbox/${token}/${entityName}/${suffix}`, viewAs, viewAsId);
  return {
    search: async (sourceId, q) => readOutcome(
      await api.post(url('lookup'), { source: sourceId, q })),
    detail: async (sourceId, id) => readOutcome(
      await api.post(url('lookup-detail'), { source: sourceId, id })),
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
