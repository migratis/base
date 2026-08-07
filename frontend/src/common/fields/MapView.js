import { useMemo, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polygon,
  Polyline,
  useMap,
} from 'react-leaflet';
// Side-effect: fixes Leaflet's default marker icon + loads the map stylesheets.
// Shared with MapField / MapDisplay; must run before any map renders.
import '../tools/mapSetup';

// -----------------------------------------------------------------------------
// MapView — the map primitive available to AI-authored custom displays.
//
// A custom display is compiled with `new Function('React', 'sanitizeHtml',
// 'MapView', ...)`, so this is the ONLY way such a component can draw a map:
// there are no imports in that scope, and the Leaflet global is not there
// either. App 2's "Tour de France" hub called `L.map(...)` behind a
// `typeof L !== 'undefined'` guard and therefore drew nothing at all, forever,
// while its own description promised an interactive OpenStreetMap.
//
// The API is deliberately one prop wide. This component is called by code that
// has never been executed before it reaches a user, so every input is treated as
// hostile: a bad geometry is dropped, not thrown.
//
//   <MapView items={[{ id, geo, label }]} height={320} onSelect={fn} />
//   <MapView geo={record.data.route} label="Étape 3" />        // one-item shorthand
//
// `geo` is a GeoJSON Point / LineString / Polygon (or its JSON string), exactly
// as a `geo` field stores it.
// -----------------------------------------------------------------------------

export const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
export const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

const DEFAULT_CENTER = [48.8566, 2.3522]; // Paris — a neutral starting view
const DEFAULT_ZOOM = 4;

// Stored as GeoJSON [lng, lat]; Leaflet wants [lat, lng].
function parseGeo(value) {
  if (!value) return null;
  let geo = value;
  if (typeof geo === 'string') {
    try {
      geo = JSON.parse(geo);
    } catch {
      return null;
    }
  }
  if (!geo || !geo.type || !Array.isArray(geo.coordinates)) return null;
  return geo;
}

const pointToLatLng = (geo) => {
  const [lng, lat] = geo.coordinates || [];
  return Number.isFinite(lat) && Number.isFinite(lng) ? [lat, lng] : null;
};
const lineToLatLngs = (geo) =>
  (geo.coordinates || [])
    .map(([lng, lat]) => (Number.isFinite(lat) && Number.isFinite(lng) ? [lat, lng] : null))
    .filter(Boolean);
const polygonToLatLngs = (geo) =>
  ((geo.coordinates && geo.coordinates[0]) || [])
    .map(([lng, lat]) => (Number.isFinite(lat) && Number.isFinite(lng) ? [lat, lng] : null))
    .filter(Boolean);

// Every [lat, lng] a geometry occupies — used to fit the view.
function anchorsOf(geo) {
  if (!geo) return [];
  if (geo.type === 'Point') {
    const p = pointToLatLng(geo);
    return p ? [p] : [];
  }
  if (geo.type === 'LineString') return lineToLatLngs(geo);
  if (geo.type === 'Polygon') return polygonToLatLngs(geo);
  return [];
}

// Leaflet has no declarative bounds prop, so fit imperatively from inside the
// container (where useMap is available).
function FitBounds({ positions }) {
  const map = useMap();
  useEffect(() => {
    if (!map || !positions.length) return;
    if (positions.length === 1) {
      map.setView(positions[0], 13);
    } else if (map.fitBounds) {
      map.fitBounds(positions, { padding: [30, 30] });
    }
  }, [map, positions]);
  return null;
}

const MapView = ({
  items,
  geo,
  label,
  height = 320,
  zoom = DEFAULT_ZOOM,
  onSelect,
  className = '',
}) => {
  // One-item shorthand, and a hard guard on the array form: a custom display
  // that passes an object (or nothing) must still render a map, not crash the
  // page it lives on.
  const list = useMemo(() => {
    if (Array.isArray(items)) return items;
    if (items && typeof items === 'object') return [items];
    if (geo) return [{ id: 'single', geo, label }];
    return [];
  }, [items, geo, label]);

  const plotted = useMemo(
    () => list
      .filter((it) => it && typeof it === 'object')
      .map((it, i) => ({ ...it, key: it.id ?? i, parsed: parseGeo(it.geo) }))
      .filter((it) => it.parsed && anchorsOf(it.parsed).length),
    [list],
  );

  const positions = useMemo(
    () => plotted.flatMap((it) => anchorsOf(it.parsed)),
    [plotted],
  );

  const popupFor = (it) => (
    it.label == null || it.label === '' ? null : (
      <Popup>
        <div className="map-popup" style={{ fontWeight: 600 }}>{String(it.label)}</div>
      </Popup>
    )
  );

  const handlers = (it) => (
    onSelect ? { click: () => onSelect(it.id) } : undefined
  );

  return (
    <div className={`map-view ${className}`.trim()}>
      <MapContainer
        center={positions[0] || DEFAULT_CENTER}
        zoom={zoom}
        scrollWheelZoom={false}
        style={{ height, width: '100%', borderRadius: 6 }}
      >
        <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />
        <FitBounds positions={positions} />
        {plotted.map((it) => {
          const { parsed } = it;
          if (parsed.type === 'Point') {
            return (
              <Marker key={it.key} position={pointToLatLng(parsed)} eventHandlers={handlers(it)}>
                {popupFor(it)}
              </Marker>
            );
          }
          if (parsed.type === 'LineString') {
            return (
              <Polyline
                key={it.key}
                positions={lineToLatLngs(parsed)}
                pathOptions={{ color: it.color || '#2b6cb0', weight: it.selected ? 6 : 4 }}
                eventHandlers={handlers(it)}
              >
                {popupFor(it)}
              </Polyline>
            );
          }
          return (
            <Polygon
              key={it.key}
              positions={polygonToLatLngs(parsed)}
              pathOptions={{ color: it.color || '#2b6cb0', weight: it.selected ? 4 : 2 }}
              eventHandlers={handlers(it)}
            >
              {popupFor(it)}
            </Polygon>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default MapView;
