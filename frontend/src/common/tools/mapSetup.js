// =============================================================================
// mapSetup.js
// One-time Leaflet setup shared by every built-in map component (MapField,
// MapDisplay). Import this module once from any component that renders a
// Leaflet map — it:
//   1. pulls in the Leaflet + Geoman stylesheets (they must be present for tile
//      / marker / toolbar layout to work), and
//   2. fixes Leaflet's default marker icon, whose relative image paths break
//      when bundled by webpack. We re-point L.Icon.Default at the bundled asset
//      URLs so markers render instead of showing broken images.
//
// Loading the vendor CSS here (rather than in the global SCSS) keeps Leaflet's
// ~150-200 KB payload out of the main bundle until a map actually mounts.
// Layout / z-index overrides for the map live in
// `common/styles/_third-party.scss`.
// =============================================================================

import L from 'leaflet';

// Geoman (draw/edit polygons & polylines) registers itself onto Leaflet's Map
// as `map.pm` on import — a one-time side effect. Import it after leaflet.
import '@geoman-io/leaflet-geoman-free';

import 'leaflet/dist/leaflet.css';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Leaflet computes icon URLs from its own script path, which webpack rewrites —
// so the built-in _getIconUrl lookup fails. Drop it and point the default icon
// at the assets webpack has fingerprinted for us.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

export default L;
