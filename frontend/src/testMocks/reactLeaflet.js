/* eslint-disable react/prop-types */
// -----------------------------------------------------------------------------
// Jest mock for `react-leaflet` (ESM-only — Jest/CRA cannot transform it, and it
// needs a real sized DOM/canvas that jsdom lacks). Mapped in via package.json
// "jest".moduleNameMapper. Every component becomes a plain <div> that records
// its props as data-attributes, and the hooks return a fake Leaflet map whose
// Geoman (`pm`) surface is stubbed. Tests drive interactions through the
// `__fire*` helpers below.
//
// Reset module-level handler state between tests with `__reset()` (CRA runs
// with resetMocks:true, which clears jest.fn() calls but NOT this closure state).
// -----------------------------------------------------------------------------
import React from 'react';

let mapClickHandlers = {}; // registered via useMapEvents
let geomanHandlers = {};   // registered via map.on('pm:*', …)

export function __reset() {
  mapClickHandlers = {};
  geomanHandlers = {};
}

const fakeMap = {
  pm: {
    addControls: jest.fn(),
    removeControls: jest.fn(),
    enableDraw: jest.fn(),
    disableDraw: jest.fn(),
    getGeomanLayers: jest.fn(() => []),
  },
  on: (evt, cb) => { geomanHandlers[evt] = cb; },
  off: (evt) => { delete geomanHandlers[evt]; },
  addLayer: jest.fn(),
  removeLayer: jest.fn(),
  setView: jest.fn(),
  fitBounds: jest.fn(),
};

export function useMap() { return fakeMap; }

export function useMapEvents(handlers) {
  mapClickHandlers = { ...mapClickHandlers, ...handlers };
  return fakeMap;
}

// --- test drivers -----------------------------------------------------------
export function __fireMapClick(lat, lng) {
  if (mapClickHandlers.click) mapClickHandlers.click({ latlng: { lat, lng } });
}
export function __fireGeoman(evt, layer) {
  if (geomanHandlers[evt]) geomanHandlers[evt]({ layer, shape: layer && layer.__shape });
}
export function __hasGeoman(evt) {
  return typeof geomanHandlers[evt] === 'function';
}

// --- component stubs --------------------------------------------------------
export function MapContainer({ children }) {
  return <div data-testid="map">{children}</div>;
}
export function TileLayer({ url, attribution }) {
  return <div data-testid="tilelayer" data-url={url} data-attribution={attribution} />;
}
export function Marker({ position, draggable, eventHandlers, children }) {
  const [lat, lng] = position || [];
  return (
    <div data-testid="marker" data-lat={lat} data-lng={lng} data-draggable={draggable ? '1' : '0'}>
      {draggable && (
        <button
          type="button"
          data-testid="marker-dragend"
          onClick={() =>
            eventHandlers &&
            eventHandlers.dragend &&
            eventHandlers.dragend({
              target: { getLatLng: () => window.__leafletDragTo || { lat: 0, lng: 0 } },
            })
          }
        >
          drag
        </button>
      )}
      {children}
    </div>
  );
}
export function Popup({ children }) {
  return <div data-testid="popup">{children}</div>;
}
export function Polygon({ positions, children }) {
  return <div data-testid="polygon" data-positions={JSON.stringify(positions)}>{children}</div>;
}
export function Polyline({ positions, children }) {
  return <div data-testid="polyline" data-positions={JSON.stringify(positions)}>{children}</div>;
}
