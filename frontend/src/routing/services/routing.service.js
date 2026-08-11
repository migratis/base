import axiosInstance from '../../common/tools/axios';
import { ROUTE_OUTCOME } from './routeOutcome';
import { sandboxAuthConfig } from './sandboxToken';

/**
 * Talking to `migratis.routing`.
 *
 * Every call here is deterministic — no AI, no credits, no confirm-spend modal.
 * It therefore rides the plain `common/tools/axios` rather than the generator's
 * AI transport: there is no model to select and nothing to price.
 *
 * The one rule this module exists to enforce is that **a failure is never read
 * as a snap**. A caller that mistakes an unreachable engine for a result stores
 * the user's traced line as though it followed roads — which is exactly the bug
 * SCOPE_road_routing.md@8914275 was written to fix, so the outcomes are named and the
 * geometry is only ever present on `SNAPPED`.
 */

// Re-exported for callers that already import this service; the canonical
// definition is `./routeOutcome`, which imports nothing.
export { ROUTE_OUTCOME };

const MIN_WAYPOINTS = 2;

// The error key the backend named, if it named one. `detail` is a list of
// {loc, msg, type} entries; `msg` carries the i18n key.
function detailKey(data) {
  const detail = data && data.detail;
  if (!Array.isArray(detail) || !detail.length) return '';
  return detail[0].msg || '';
}

function isLineString(data) {
  return Boolean(data && data.type === 'LineString' && Array.isArray(data.coordinates));
}

// Both shapes have to be handled: the shared axios rejects on a non-2xx, but a
// mocked/intercepted instance can resolve with one. Normalise before deciding.
function responseOf(errorOrResponse) {
  if (errorOrResponse && errorOrResponse.response) return errorOrResponse.response;
  if (errorOrResponse && typeof errorOrResponse.status === 'number') return errorOrResponse;
  return null;
}

function outcomeFor(response) {
  const key = detailKey(response.data);
  if (response.status === 503) {
    return key === 'routing-engine-not-configured'
      ? { outcome: ROUTE_OUTCOME.NOT_CONFIGURED, key }
      : { outcome: ROUTE_OUTCOME.UNAVAILABLE, key: key || 'routing-engine-unavailable' };
  }
  if (response.status === 422) {
    return {
      outcome: key === 'route-not-found' ? ROUTE_OUTCOME.NO_ROUTE : ROUTE_OUTCOME.NOT_A_ROUTE,
      key: key || 'route-not-found',
      engineReason: (response.data && response.data.engine_reason) || '',
    };
  }
  // Everything else — including a refused caller (403) and a spent per-caller
  // allowance (429) — is UNAVAILABLE, and deliberately so. Those are capacity
  // answers, not route answers: telling the user no route exists would send
  // them to move a waypoint that was never the problem
  // (SCOPE_routing_sandbox_external.md@c170e1a §5.4). The backend's own key is carried
  // through so the reason survives into the badge.
  return { outcome: ROUTE_OUTCOME.UNAVAILABLE, key: key || 'routing-engine-unavailable' };
}

/**
 * Snap waypoints (GeoJSON `[lng, lat]` order) to the road network.
 *
 * @returns {Promise<{outcome: string, geometry?: object, key?: string, engineReason?: string}>}
 *          `geometry` is present only on SNAPPED, and is the §4 shape: a plain
 *          LineString carrying its waypoints as a `routing` foreign member.
 */
export async function snapRoute(waypoints, profile) {
  if (!Array.isArray(waypoints) || waypoints.length < MIN_WAYPOINTS) {
    return { outcome: ROUTE_OUTCOME.NOT_A_ROUTE, key: 'route-needs-two-waypoints' };
  }

  let response;
  try {
    // The sandbox token rides as a header, added here rather than by the caller
    // so a future caller cannot forget it — on migratis a snap without one is
    // refused, and the line would quietly go straight (§6).
    response = await axiosInstance.post(
      'routing/snap',
      { waypoints, profile },
      sandboxAuthConfig()
    );
  } catch (err) {
    response = responseOf(err);
    if (!response) {
      return { outcome: ROUTE_OUTCOME.UNAVAILABLE, key: 'routing-engine-unavailable' };
    }
  }

  if (response.status === 200) {
    // Status is checked before the body, then the body is checked for the shape
    // it must have: a gateway answering 200 with HTML would otherwise be stored
    // as the record's geometry.
    return isLineString(response.data)
      ? { outcome: ROUTE_OUTCOME.SNAPPED, geometry: response.data }
      : { outcome: ROUTE_OUTCOME.UNAVAILABLE, key: 'routing-engine-unavailable' };
  }
  return outcomeFor(response);
}

// --------------------------------------------------------------------------- //
// Availability
// --------------------------------------------------------------------------- //
// Asked once per page load and shared: a form with six route fields must not
// probe the engine six times, and the answer cannot change mid-edit in a way
// worth chasing — a snap that fails afterwards degrades on its own.
let availabilityPromise = null;

const ABSENT = { available: false, state: 'not_configured', engine: null, profiles: [] };

export function resetAvailabilityCache() {
  availabilityPromise = null;
}

export function fetchAvailability() {
  if (!availabilityPromise) {
    availabilityPromise = (async () => {
      let response;
      try {
        response = await axiosInstance.get('routing/availability');
      } catch (err) {
        response = responseOf(err);
        if (!response) {
          return { ...ABSENT, state: 'unavailable' };
        }
      }
      if (response.status === 404) {
        // The router is not mounted — the module is not installed on this host.
        // That is "not configured", not "broken": show nothing.
        return { ...ABSENT };
      }
      if (response.status !== 200 || !response.data) {
        return { ...ABSENT, state: 'unavailable' };
      }
      const data = response.data;
      return {
        available: Boolean(data.available),
        state: data.state || 'unavailable',
        engine: data.engine || null,
        profiles: Array.isArray(data.profiles) ? data.profiles : [],
      };
    })();
  }
  return availabilityPromise;
}
