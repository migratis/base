import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Marker, Polyline, useMapEvents } from 'react-leaflet';

import { fetchAvailability, snapRoute } from '../services/routing.service';
import { ROUTE_OUTCOME } from '../services/routeOutcome';

/**
 * The waypoint-editing layer for a `geo` field in geo_mode='route'.
 *
 * Rendered *inside* MapField's `<MapContainer>`, in place of MapField's own
 * tracing layer, whenever the routing module is present. It is the only place
 * in the frontend that knows a road graph exists.
 *
 * Two ideas do all the work here:
 *
 * 1. **The waypoints are the feature.** A snapped route is 800 anonymous
 *    vertices; nobody can drag waypoint 3 of that. So the markers are the
 *    waypoints (a handful) and the drawn line is the snapped geometry — the two
 *    are stored together, the waypoints riding as a `routing` foreign member on
 *    the geometry (SCOPE_road_routing.md §4).
 *
 * 2. **Degrade with a name.** Installing a Django app cannot start a routing
 *    container, so an engine that is absent, down, or unable to route is the
 *    normal case, not the exception. Absent ⇒ this component steps aside and
 *    the field traces exactly as it did before routing existed. Down or unable
 *    ⇒ the user's edit is *kept* as a straight line and badged with the reason.
 *    A straight line that says nothing is the bug this module was written to
 *    fix, so it is the one outcome that must not exist.
 */

const MAX_WAYPOINTS = 100;      // mirrors services.MAX_WAYPOINTS on the backend

const round6 = (n) => Math.round((parseFloat(n) || 0) * 1e6) / 1e6;

/**
 * The editable waypoints behind a stored value.
 *
 * A value written by this component carries them explicitly. A line stored
 * before routing existed carries none — and its vertices *are* what its author
 * clicked, so they are adopted as waypoints. Nothing is re-snapped on the
 * strength of that: §9 is explicit that stored straight lines are not
 * retro-snapped, so the geometry only changes once the user edits it.
 */
export function waypointsOf(geo) {
  if (!geo) return [];
  const stored = geo.routing && geo.routing.waypoints;
  if (Array.isArray(stored) && stored.length) return stored;
  const coordinates = Array.isArray(geo.coordinates) ? geo.coordinates : [];
  return coordinates.length && coordinates.length <= MAX_WAYPOINTS ? coordinates : [];
}

const toLatLngs = (coordinates) => (coordinates || []).map(([lng, lat]) => [lat, lng]);

/** The straight line kept when the engine cannot answer. */
export function unsnappedGeometry(waypoints, profile) {
  return {
    type: 'LineString',
    coordinates: waypoints,
    routing: {
      waypoints,
      profile,
      // Explicitly *not* road-following. `snapped_at` is what a reader uses to
      // tell a snapped route from a straight one; writing it here would make
      // the value claim something untrue and would hide the failure forever.
      snapped: false,
    },
  };
}

function MapClicks({ onPick }) {
  useMapEvents({ click: (e) => onPick(e.latlng) });
  return null;
}

const RouteEditor = ({ geo, setGeo, readOnly = false, profile = 'bicycle', fallback = null }) => {
  const { t } = useTranslation('common');
  const [availability, setAvailability] = useState(null);
  const [failure, setFailure] = useState(null);
  const [snapping, setSnapping] = useState(false);
  // The very first waypoint of a brand-new route, held here and not written.
  // A one-position LineString is not valid GeoJSON, and every reader in both
  // repos would have to learn to survive one; the marker is on screen, the
  // field simply stays empty until there is a route to store.
  const [pending, setPending] = useState([]);
  // Guards against a slow snap landing after a newer one and overwriting it.
  const snapSeq = useRef(0);

  useEffect(() => {
    let alive = true;
    fetchAvailability().then((state) => {
      if (alive) setAvailability(state);
    });
    return () => { alive = false; };
  }, []);

  const stored = useMemo(() => waypointsOf(geo), [geo]);
  const waypoints = stored.length ? stored : pending;
  const line = useMemo(
    () => toLatLngs((geo && Array.isArray(geo.coordinates) && geo.coordinates) || []),
    [geo]
  );

  const commit = useCallback(
    async (next) => {
      const seq = (snapSeq.current += 1);
      setSnapping(true);
      const result = await snapRoute(next, profile);
      if (seq !== snapSeq.current) return;      // superseded by a newer edit
      setSnapping(false);

      if (result.outcome === ROUTE_OUTCOME.SNAPPED) {
        setFailure(null);
        setGeo(result.geometry);
        return;
      }
      // The edit is never discarded: the user moved a waypoint and that has to
      // survive, whatever the engine did.
      setFailure(result);
      setGeo(unsnappedGeometry(next, profile));
    },
    [profile, setGeo]
  );

  const apply = useCallback(
    (next) => {
      if (next.length < 2) {
        setPending(next);      // not a route yet — shown, not stored
        return;
      }
      setPending([]);
      commit(next);
    },
    [commit]
  );

  const onPick = useCallback(
    (latlng) => {
      if (readOnly || waypoints.length >= MAX_WAYPOINTS) return;
      apply([...waypoints, [round6(latlng.lng), round6(latlng.lat)]]);
    },
    [apply, readOnly, waypoints]
  );

  const onDrag = useCallback(
    (index) => (event) => {
      if (readOnly) return;
      const ll = event.target.getLatLng();
      apply(waypoints.map((point, i) =>
        (i === index ? [round6(ll.lng), round6(ll.lat)] : point)));
    },
    [apply, readOnly, waypoints]
  );

  // The engine is not configured on this host: step aside entirely. The field
  // traces as it always did and nothing on screen mentions routing, because
  // nothing was asked for.
  if (availability && availability.state === 'not_configured') return fallback;

  // Still probing — draw what is stored, offer no controls for the moment.
  const ready = Boolean(availability);
  const distanceM = geo && geo.routing && geo.routing.distance_m;

  return (
    <>
      {ready && !readOnly && <MapClicks onPick={onPick} />}
      {line.length > 1 && <Polyline positions={line} />}
      {waypoints.map((point, index) => (
        <Marker
          key={`wp-${index}-${point[0]}-${point[1]}`}
          position={[point[1], point[0]]}
          draggable={ready && !readOnly}
          eventHandlers={{ dragend: onDrag(index) }}
        />
      ))}

      {/* One overlay, drawn over the map rather than under it, and mounted only
          once availability is known — until then the component does not yet
          know whether it is the editor or a bystander, and must claim neither.
          MapContainer renders non-Leaflet children inside its own div, so this
          positions against the map without a portal. */}
      {ready && (
        <div className="route-overlay" data-testid="route-overlay">
          {failure && (
            <span className="route-badge" data-testid="route-badge">
              {failure.outcome === ROUTE_OUTCOME.NO_ROUTE
                ? t('route-no-route', 'Straight line — no route found')
                : t('route-unavailable', 'Straight line — routing unavailable')}
              {failure.engineReason ? ` (${failure.engineReason})` : ''}
            </span>
          )}

          {!failure && typeof distanceM === 'number' && (
            <span className="route-distance" data-testid="route-distance">
              {(distanceM / 1000).toFixed(1)} {t('route-km', 'km')}
            </span>
          )}

          {snapping && (
            <span className="route-snapping" data-testid="route-snapping">
              {t('route-snapping', 'Following roads…')}
            </span>
          )}
        </div>
      )}
    </>
  );
};

export default RouteEditor;
