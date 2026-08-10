import RouteEditor from './components/RouteEditor';
import { ROUTING } from '../settings';

/**
 * Routing's contribution to the app shell. Discovered automatically by
 * common/shell/registry.js.
 *
 * One slot only: the waypoint-editing layer `MapField` renders inside its map
 * when a `geo` field is in geo_mode='route'. `common/` owns the field and must
 * not import this module, so the dependency runs the other way — which is also
 * what makes the module genuinely optional. Nothing else in the frontend knows
 * a road graph exists.
 *
 * The `ROUTING` flag only says the module is installed; whether waypoint mode
 * actually appears is measured at runtime against GET /routing/availability,
 * because a host can install the app and run no engine
 * (SCOPE_road_routing.md §10).
 */
export const routeSnappers = [
  {
    id: 'routing',
    order: 10,
    enabled: () => ROUTING,
    Editor: RouteEditor,
  },
];
