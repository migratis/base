// -----------------------------------------------------------------------------
// geoSummary — the one-line reading of a `geo` value, for the surfaces that
// cannot draw a map.
//
// A `geo` field stores GeoJSON (as a JSON string inside `record.data`), and the
// form edits it on a real Leaflet map. Every ROW display — table, list, cards —
// formats cell values as text, so a geo column used to fall through to
// `String(value)` and print `{"type":"Point","coordinates":[…]}` at the user.
// App 2's "Tour de France" shipped exactly that: `Climb.summit` modelled
// correctly, drawn on a map in the form, raw JSON in the embedded list.
//
// This is deliberately NOT a map: one Leaflet container per row is a heavy,
// unreadable answer to "which summit is this". The map routes are the entity's
// display_mode 'map' (MapDisplay) and a custom_display calling `MapView` — see
// the `geo_field_not_displayed` advisory. This helper is what the remaining
// text surfaces show, and it is shared so they cannot drift apart.
// -----------------------------------------------------------------------------

const _finite = (n) => Number.isFinite(n);

// GeoJSON orders a position [lng, lat]; humans read "lat, lng".
const _asLatLng = (pos) => {
  if (!Array.isArray(pos)) return null;
  const [lng, lat] = pos;
  return _finite(lat) && _finite(lng) ? [lat, lng] : null;
};

const _round = (n) => String(Math.round(n * 10000) / 10000);

const _ringOf = (geo) => {
  const ring = geo.type === 'Polygon' ? (geo.coordinates || [])[0] : geo.coordinates;
  return Array.isArray(ring) ? ring.filter((p) => _asLatLng(p)) : [];
};

/**
 * Summarise a stored geo value.
 *
 * @param   {string|object} value  GeoJSON, or its JSON string, as stored.
 * @returns {null|{type: string, text: ?string, count: number}}
 *          `text` carries "lat, lng" for a Point and is null for a geometry
 *          whose reading is its vertex `count`. Null when there is nothing
 *          plottable — an empty, malformed or unsupported geometry — so the
 *          caller shows its own empty marker rather than the raw value.
 */
export function geoSummary(value) {
  if (!value) return null;
  let geo = value;
  if (typeof geo === 'string') {
    try {
      geo = JSON.parse(geo);
    } catch {
      return null;
    }
  }
  if (!geo || typeof geo !== 'object' || !Array.isArray(geo.coordinates)) return null;

  if (geo.type === 'Point') {
    const latLng = _asLatLng(geo.coordinates);
    if (!latLng) return null;
    return { type: 'Point', text: `${_round(latLng[0])}, ${_round(latLng[1])}`, count: 1 };
  }

  if (geo.type === 'LineString' || geo.type === 'Polygon') {
    const ring = _ringOf(geo);
    if (!ring.length) return null;
    // A Polygon ring is closed — its last position repeats the first — and
    // counting that repeat would report a square as five corners.
    let count = ring.length;
    if (geo.type === 'Polygon' && count > 1
        && JSON.stringify(ring[0]) === JSON.stringify(ring[count - 1])) {
      count -= 1;
    }
    return { type: geo.type, text: null, count };
  }

  return null;
}

/**
 * Is this column a geo column? The field type is authoritative; `render_as`
 * 'map' covers a config whose field descriptor never carried the type.
 */
export function isGeoField(field, fieldConfig) {
  return (field?.field_type === 'geo') || (fieldConfig?.render_as === 'map');
}

export default geoSummary;
