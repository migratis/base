/**
 * What a snap attempt actually did.
 *
 * Kept in its own module with no imports so a consumer — or a test — can name
 * an outcome without dragging in the axios instance (and, through it, the
 * i18next HTTP backend). Same separation as the generator's `aiOutcome.js`.
 *
 * The distinctions are not cosmetic. `NOT_CONFIGURED` hides the waypoint
 * affordance entirely because the feature was never asked for on this host;
 * `UNAVAILABLE` keeps it and badges it, because it *was* asked for and is down.
 * Collapsing the two produces a straight line with no explanation, which is the
 * bug SCOPE_road_routing.md exists to fix.
 */
export const ROUTE_OUTCOME = {
  SNAPPED: 'snapped',
  NO_ROUTE: 'no-route',
  UNAVAILABLE: 'unavailable',
  NOT_CONFIGURED: 'not-configured',
  NOT_A_ROUTE: 'not-a-route',
};

export default ROUTE_OUTCOME;
