import { useMemo, useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polygon,
  Polyline,
  useMap,
} from 'react-leaflet';
// Side-effect: fixes Leaflet's default marker icon + loads the map/Geoman
// stylesheets. Shared with MapField; must run before any map renders.
import '../../tools/mapSetup';
import InteractionRowActions from '../InteractionRowActions';

// -----------------------------------------------------------------------------
// Constants (kept in step with MapField)
// -----------------------------------------------------------------------------
export const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
export const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

const DEFAULT_CENTER = [48.8566, 2.3522]; // Paris — a neutral starting view
const DEFAULT_ZOOM = 3;

// -----------------------------------------------------------------------------
// Pure GeoJSON helpers — stored [lng, lat], Leaflet wants [lat, lng].
// Kept self-contained (this file is synced into base/ on its own).
// -----------------------------------------------------------------------------
function parseGeo(value) {
  if (!value) return null;
  try {
    const g = typeof value === 'string' ? JSON.parse(value) : value;
    return g && g.type && Array.isArray(g.coordinates) ? g : null;
  } catch {
    return null;
  }
}

const pointToLatLng = (geo) => {
  const [lng, lat] = geo.coordinates || [];
  return [lat, lng];
};
const polygonToLatLngs = (geo) =>
  ((geo.coordinates && geo.coordinates[0]) || []).map(([lng, lat]) => [lat, lng]);
const lineToLatLngs = (geo) => (geo.coordinates || []).map(([lng, lat]) => [lat, lng]);

// A representative [lat, lng] for any geometry (first vertex), or null.
function geoAnchor(geo) {
  if (!geo) return null;
  if (geo.type === 'Point') return pointToLatLng(geo);
  if (geo.type === 'Polygon') return polygonToLatLngs(geo)[0] || null;
  if (geo.type === 'LineString') return lineToLatLngs(geo)[0] || null;
  return null;
}

// The entity's geographic field: an explicit config override wins, else the
// first field typed `geo` (mirrors CalendarDisplay's start-field detection).
function detectGeoField(entity, config) {
  const explicit = (config?.display_mode_options?.map || {}).geo_field;
  if (explicit) return explicit;
  const fields = entity?.fields || [];
  return (fields.find((f) => f.field_type === 'geo') || {}).name || null;
}

// A human label for a record's popup — prefer the configured display labels,
// then a name/title-ish field, then the id.
function detectTitleField(entity, config) {
  const labels = config?.display_label_fields || [];
  if (labels.length) return labels[0];
  const fields = entity?.fields || [];
  for (const c of ['name', 'title', 'label', 'subject']) {
    if (fields.find((f) => f.name === c)) return c;
  }
  return null;
}

// Imperatively fit the map to every plotted geometry (Leaflet has no
// declarative bounds prop). Lives inside <MapContainer> so it can call useMap.
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

// -----------------------------------------------------------------------------
// MapDisplay — plots every record's geo field, one popup per record.
// Receives the standard display props threaded by the sandbox host and the
// generated {Name}List container (kept identical via the display-sync hook).
// -----------------------------------------------------------------------------
const MapDisplay = ({
  entity,
  records = [],
  config = {},
  onEdit,
  onDelete,
  onInteraction,
  viewAs,
  getRoleRank,
  t,
}) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback || key);

  const geoField = detectGeoField(entity, config);
  const titleField = detectTitleField(entity, config);

  // Parse each record into a plotted geometry (dropping the geometry-less ones).
  const plotted = useMemo(() => {
    if (!geoField) return [];
    return records
      .map((record) => ({ record, geo: parseGeo(record?.data?.[geoField]) }))
      .filter((p) => p.geo);
  }, [records, geoField]);

  const anchors = useMemo(
    () => plotted.map((p) => geoAnchor(p.geo)).filter(Boolean),
    [plotted],
  );

  const renderPopup = (record) => {
    const title = titleField ? record.data[titleField] : null;
    return (
      <Popup>
        <div className="map-popup">
          {title != null && title !== '' && (
            <div style={{ fontWeight: 600, marginBottom: 4 }}>{String(title)}</div>
          )}
          <InteractionRowActions
            interactions={config?.interactions}
            recordData={record?.data}
            recordId={record.id}
            viewAs={viewAs}
            getRoleRank={getRoleRank}
            onInteraction={onInteraction}
            className="d-flex flex-wrap gap-1 mb-1"
          />
          <div className="d-flex flex-wrap gap-1">
            {onEdit && (
              <Button size="sm" variant="outline-primary" onClick={() => onEdit(record)}>
                {tval('edit', 'Edit')}
              </Button>
            )}
            {onDelete && (
              <Button size="sm" variant="outline-danger" onClick={() => onDelete(record.id)}>
                {tval('delete', 'Delete')}
              </Button>
            )}
          </div>
        </div>
      </Popup>
    );
  };

  if (!geoField) {
    return (
      <div className="text-center text-muted py-4">
        {tval('map-no-geo-field', 'This view needs a geographic (map) field to plot records.')}
      </div>
    );
  }

  const center = anchors[0] || DEFAULT_CENTER;

  return (
    <div className="map-display">
      <MapContainer
        center={center}
        zoom={anchors.length ? 13 : DEFAULT_ZOOM}
        scrollWheelZoom={false}
        className="leaflet-container"
      >
        <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />
        <FitBounds positions={anchors} />

        {plotted.map(({ record, geo }) => {
          if (geo.type === 'Point') {
            return (
              <Marker key={record.id} position={pointToLatLng(geo)}>
                {renderPopup(record)}
              </Marker>
            );
          }
          if (geo.type === 'Polygon') {
            return (
              <Polygon key={record.id} positions={polygonToLatLngs(geo)}>
                {renderPopup(record)}
              </Polygon>
            );
          }
          if (geo.type === 'LineString') {
            return (
              <Polyline key={record.id} positions={lineToLatLngs(geo)}>
                {renderPopup(record)}
              </Polyline>
            );
          }
          return null;
        })}
      </MapContainer>

      {records.length === 0 && (
        <div className="text-center text-muted py-4">
          {tval('no-records', 'No records')}
        </div>
      )}
    </div>
  );
};

export default MapDisplay;
