import { useMemo, useEffect, useCallback } from 'react';
import { useFormContext, useController } from 'react-hook-form';
import Button from 'react-bootstrap/Button';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polygon,
  Polyline,
  useMap,
  useMapEvents,
} from 'react-leaflet';
// Side-effect: fixes Leaflet's default marker icon + loads the map stylesheets
// and Geoman (map.pm). Must be imported before any map renders.
import '../tools/mapSetup';

// -----------------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------------
export const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
export const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
export const GEO_MODES = ['point', 'area', 'route'];

const DEFAULT_CENTER = [48.8566, 2.3522]; // Paris — a neutral starting view
const DEFAULT_ZOOM = 4;
const FOCUS_ZOOM = 13;

// -----------------------------------------------------------------------------
// Pure GeoJSON helpers (exported for unit testing)
// -----------------------------------------------------------------------------
// Coordinates are stored GeoJSON-style: [lng, lat]. Leaflet uses [lat, lng], so
// every crossing of that boundary flips the pair. We round to 6 decimals
// (~0.1 m) to keep stored values compact and stable across round-trips.
const round6 = (n) => Math.round((parseFloat(n) || 0) * 1e6) / 1e6;

export function pointGeoJSON(lng, lat, properties = {}) {
  return {
    type: 'Point',
    coordinates: [round6(lng), round6(lat)],
    properties: { ...properties },
  };
}

// latlngs: array of [lat, lng] pairs. Emits a closed [lng, lat] ring.
export function polygonGeoJSON(latlngs) {
  const ring = (latlngs || []).map(([lat, lng]) => [round6(lng), round6(lat)]);
  if (ring.length) {
    const first = ring[0];
    const last = ring[ring.length - 1];
    if (first[0] !== last[0] || first[1] !== last[1]) ring.push([...first]);
  }
  return { type: 'Polygon', coordinates: [ring] };
}

// latlngs: ordered array of [lat, lng] waypoints (itinerary sequence preserved).
export function lineStringGeoJSON(latlngs) {
  return {
    type: 'LineString',
    coordinates: (latlngs || []).map(([lat, lng]) => [round6(lng), round6(lat)]),
  };
}

export function parseGeo(value) {
  if (!value) return null;
  try {
    const g = typeof value === 'string' ? JSON.parse(value) : value;
    return g && g.type ? g : null;
  } catch {
    return null;
  }
}

// GeoJSON [lng, lat] geometry -> Leaflet [lat, lng] positions for rendering.
function pointToLatLng(geo) {
  const [lng, lat] = geo.coordinates || [];
  return [lat, lng];
}
function polygonToLatLngs(geo) {
  return ((geo.coordinates && geo.coordinates[0]) || []).map(([lng, lat]) => [lat, lng]);
}
function lineToLatLngs(geo) {
  return (geo.coordinates || []).map(([lng, lat]) => [lat, lng]);
}

// A reasonable map center for an existing geometry (first vertex), else null.
export function geoCenter(geo) {
  if (!geo) return null;
  if (geo.type === 'Point') return pointToLatLng(geo);
  if (geo.type === 'Polygon') return polygonToLatLngs(geo)[0] || null;
  if (geo.type === 'LineString') return lineToLatLngs(geo)[0] || null;
  return null;
}

// -----------------------------------------------------------------------------
// Map-interaction children (must live inside <MapContainer>)
// -----------------------------------------------------------------------------
function MapClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng);
    },
  });
  return null;
}

// Enables the Geoman draw/edit toolbar for the active geo_mode and reports the
// drawn/edited geometry. Only mounted in editable area/route mode.
function GeomanEditor({ geoMode, onShape }) {
  const map = useMap();
  useEffect(() => {
    if (!map || !map.pm) return undefined;
    map.pm.addControls({
      position: 'topleft',
      drawMarker: false,
      drawCircle: false,
      drawCircleMarker: false,
      drawRectangle: false,
      drawText: false,
      drawPolygon: geoMode === 'area',
      drawPolyline: geoMode === 'route',
      editMode: true,
      dragMode: false,
      cutPolygon: false,
      rotateMode: false,
      removalMode: true,
    });
    const handle = (e) => {
      if (e && e.layer && typeof e.layer.toGeoJSON === 'function') {
        const feature = e.layer.toGeoJSON();
        if (feature && feature.geometry) onShape(feature.geometry);
      }
    };
    map.on('pm:create', handle);
    map.on('pm:update', handle);
    return () => {
      map.off('pm:create', handle);
      map.off('pm:update', handle);
      if (map.pm.removeControls) map.pm.removeControls();
    };
  }, [map, geoMode, onShape]);
  return null;
}

// -----------------------------------------------------------------------------
// MapField
// -----------------------------------------------------------------------------
const MapField = ({
  name,
  label,
  required = false,
  help = null,
  disabled = false,
  readOnly = false,
  geoMode = 'point',
}) => {
  const mode = GEO_MODES.includes(geoMode) ? geoMode : 'point';
  const ro = disabled || readOnly;

  const { control } = useFormContext();
  const { field } = useController({ name, control, defaultValue: '' });

  const geo = useMemo(() => parseGeo(field.value), [field.value]);

  const setGeo = useCallback(
    (g) => field.onChange(g ? JSON.stringify(g) : ''),
    [field]
  );

  const onPickPoint = useCallback(
    (latlng) => {
      const prev = parseGeo(field.value);
      setGeo(pointGeoJSON(latlng.lng, latlng.lat, (prev && prev.properties) || {}));
    },
    [field.value, setGeo]
  );

  const onDragPoint = useCallback(
    (e) => {
      const ll = e.target.getLatLng();
      const prev = parseGeo(field.value);
      setGeo(pointGeoJSON(ll.lng, ll.lat, (prev && prev.properties) || {}));
    },
    [field.value, setGeo]
  );

  const onShape = useCallback((geometry) => {
    if (geometry) setGeo(geometry);
  }, [setGeo]);

  const center = useMemo(() => geoCenter(geo) || DEFAULT_CENTER, [geo]);

  return (
    <div className="migratis-field map-field">
      {label && (
        <label className="form-label">
          {label}
          {required && <span style={{ color: 'red' }}>&nbsp;*</span>}
        </label>
      )}

      <MapContainer
        center={center}
        zoom={geo ? FOCUS_ZOOM : DEFAULT_ZOOM}
        scrollWheelZoom={false}
        className="leaflet-container"
      >
        <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />

        {mode === 'point' && (
          <>
            {!ro && <MapClickHandler onPick={onPickPoint} />}
            {geo && geo.type === 'Point' && (
              <Marker
                position={pointToLatLng(geo)}
                draggable={!ro}
                eventHandlers={{ dragend: onDragPoint }}
              >
                {geo.properties && geo.properties.label && (
                  <Popup>{geo.properties.label}</Popup>
                )}
              </Marker>
            )}
          </>
        )}

        {mode === 'area' && (
          <>
            {geo && geo.type === 'Polygon' && <Polygon positions={polygonToLatLngs(geo)} />}
            {!ro && <GeomanEditor geoMode="area" onShape={onShape} />}
          </>
        )}

        {mode === 'route' && (
          <>
            {geo && geo.type === 'LineString' && <Polyline positions={lineToLatLngs(geo)} />}
            {!ro && <GeomanEditor geoMode="route" onShape={onShape} />}
          </>
        )}
      </MapContainer>

      {!ro && geo && (
        <Button
          size="sm"
          variant="outline-danger"
          className="mt-1"
          data-testid="map-clear"
          onClick={() => setGeo(null)}
        >
          ✕ Clear
        </Button>
      )}

      {help && <small className="form-text text-muted">{help}</small>}
    </div>
  );
};

export default MapField;
