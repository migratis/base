import { useMemo, useState } from 'react';
import {
  IoSettingsOutline as EditIcon,
  IoTrashOutline as TrashIcon,
} from 'react-icons/io5';
import InteractionRowActions from '../InteractionRowActions';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const toNum = (v) => {
  const n = parseFloat(v);
  return isNaN(n) ? null : n;
};

/**
 * Resolve a field name from config options, trying several candidate names.
 * Returns the first candidate found in entity fields, or null.
 */
const detectField = (fields, candidates) => {
  for (const c of candidates) {
    if (fields.find((f) => f.name === c)) return c;
  }
  return null;
};

/**
 * Derive a CSS color from a field value.
 * Accepts hex strings (#abc, #aabbcc) or falls back to a deterministic palette.
 */
const PALETTE = [
  '#4caf50', '#2196f3', '#ff9800', '#e91e63',
  '#9c27b0', '#00bcd4', '#795548', '#607d8b',
];
const paletteFor = (() => {
  const cache = {};
  let idx = 0;
  return (value) => {
    if (!value) return PALETTE[0];
    const key = String(value);
    if (key.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i)) return key;
    if (!(key in cache)) {
      cache[key] = PALETTE[idx % PALETTE.length];
      idx++;
    }
    return cache[key];
  };
})();

/** Compute optimal plant count for a square given spacing. */
const computeCapacity = (width, height, spacing) => {
  if (!width || !height || !spacing || spacing <= 0) return null;
  const cols = Math.floor(width / spacing);
  const rows = Math.floor(height / spacing);
  return cols > 0 && rows > 0 ? cols * rows : null;
};

/** Determine readable text color (black or white) against a background. */
const contrastColor = (hex) => {
  try {
    const h = hex.replace('#', '');
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    // luminance formula
    return (r * 299 + g * 587 + b * 114) / 1000 > 128 ? '#222' : '#fff';
  } catch {
    return '#fff';
  }
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const GridCell = ({
  record, cellW, cellH, labelField, colorValue, spacing,
  onEdit, onDelete,
  interactions, viewAs, getRoleRank, onInteraction,
  t,
}) => {
  const [hovered, setHovered] = useState(false);

  const bgColor   = paletteFor(colorValue);
  const textColor = contrastColor(bgColor);

  const label = labelField ? String(record.data[labelField] ?? '') : '';

  const w = toNum(record.data['width']) ?? toNum(record.data['w']) ?? null;
  const h = toNum(record.data['height']) ?? toNum(record.data['h']) ?? null;
  const sp = toNum(record.data[spacing]) ?? null;
  const capacity = computeCapacity(w, h, sp);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => onEdit(record)}
      style={{
        width:           cellW,
        height:          cellH,
        background:      bgColor,
        border:          `2px solid ${hovered ? textColor : 'rgba(0,0,0,0.2)'}`,
        borderRadius:    '4px',
        cursor:          'pointer',
        display:         'flex',
        flexDirection:   'column',
        alignItems:      'center',
        justifyContent:  'center',
        padding:         '4px',
        overflow:        'hidden',
        position:        'relative',
        boxShadow:       hovered ? '0 2px 8px rgba(0,0,0,0.25)' : 'none',
        transition:      'box-shadow 0.15s, border-color 0.15s',
        userSelect:      'none',
      }}
    >
      {/* Label */}
      {label && (
        <div style={{
          color:         textColor,
          fontWeight:    600,
          fontSize:      Math.min(cellW, cellH) > 80 ? '0.8rem' : '0.65rem',
          textAlign:     'center',
          overflow:      'hidden',
          textOverflow:  'ellipsis',
          whiteSpace:    'nowrap',
          maxWidth:      '100%',
        }}>
          {label}
        </div>
      )}

      {/* Dimensions */}
      {w && h && (
        <div style={{ color: textColor, fontSize: '0.6rem', opacity: 0.85 }}>
          {w}×{h} cm
        </div>
      )}

      {/* Plant capacity */}
      {capacity !== null && (
        <div style={{
          color:      textColor,
          fontSize:   '0.6rem',
          opacity:    0.9,
          marginTop:  '2px',
          background: 'rgba(0,0,0,0.15)',
          borderRadius: '3px',
          padding:    '0 4px',
        }}>
          ×{capacity} plants
        </div>
      )}

      {/* Action icons — visible on hover */}
      {hovered && (
        <div
          style={{
            position:  'absolute',
            top:       2,
            right:     2,
            display:   'flex',
            gap:       '2px',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <span
            className="link action"
            style={{ fontSize: '0.9rem', color: textColor, opacity: 0.85 }}
            onClick={() => onEdit(record)}
          >
            <EditIcon />
          </span>
          <span
            className="link action"
            style={{ fontSize: '0.9rem', color: textColor, opacity: 0.85 }}
            onClick={() => onDelete(record.id)}
          >
            <TrashIcon />
          </span>
        </div>
      )}

      {/* Workflow buttons — visible on hover. Anchored bottom-center so they
          don't fight the top-right edit/delete icons; flex-wrap handles the
          small-cell case gracefully. */}
      {hovered && (
        <div
          style={{
            position: 'absolute',
            bottom:   2,
            left:     2,
            right:    2,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <InteractionRowActions
            interactions={interactions}
            recordData={record?.data}
            recordId={record.id}
            viewAs={viewAs}
            getRoleRank={getRoleRank}
            onInteraction={onInteraction}
            className="d-flex flex-wrap gap-1 justify-content-center"
          />
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const GridDisplay = ({
  entity,
  records,
  config = {},
  onEdit,
  onDelete,
  onInteraction,
  viewAs,
  getRoleRank,
  t,
}) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback || key);

  const opts   = config?.display_mode_options || {};
  const fields = entity?.fields || [];

  // Resolve field names — prefer explicit config, fall back to auto-detection.
  const xField       = opts.grid_x_field       || detectField(fields, ['x', 'col', 'column', 'pos_x', 'position_x', 'left']);
  const yField       = opts.grid_y_field       || detectField(fields, ['y', 'row', 'pos_y', 'position_y', 'top']);
  const widthField   = opts.grid_width_field   || detectField(fields, ['width', 'w', 'size_x', 'cols', 'span_x']);
  const heightField  = opts.grid_height_field  || detectField(fields, ['height', 'h', 'size_y', 'rows', 'span_y']);
  const colorField   = opts.grid_color_field   || detectField(fields, ['color', 'colour', 'plant_color', 'hex_color']);
  const labelField   = opts.grid_label_field   || detectField(fields, ['name', 'title', 'label', 'plant_name']);
  const spacingField = opts.grid_spacing_field || detectField(fields, ['spacing', 'plant_spacing', 'distance', 'interval']);

  const hasCoords = xField && yField;

  // ---------------------------------------------------------------------------
  // Spatial layout — records with x/y coordinates
  // ---------------------------------------------------------------------------
  const spatialData = useMemo(() => {
    if (!hasCoords || !records.length) return null;

    const items = records.map((r) => ({
      record: r,
      x:      toNum(r.data[xField])      ?? 0,
      y:      toNum(r.data[yField])      ?? 0,
      w:      toNum(r.data[widthField])  ?? 50,
      h:      toNum(r.data[heightField]) ?? 50,
    }));

    // Compute bounding box of all records
    const minX = Math.min(...items.map((i) => i.x));
    const minY = Math.min(...items.map((i) => i.y));
    const maxX = Math.max(...items.map((i) => i.x + i.w));
    const maxY = Math.max(...items.map((i) => i.y + i.h));

    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;

    return { items, minX, minY, rangeX, rangeY };
  }, [records, xField, yField, widthField, heightField, hasCoords]);

  // ---------------------------------------------------------------------------
  // Flow layout — records without coordinates (uniform grid)
  // ---------------------------------------------------------------------------
  const CELL_SIZE = 120; // px for flow layout cells
  const CANVAS_W  = 640; // px — fixed canvas width for spatial layout
  const CANVAS_H  = 480; // px

  if (!records || records.length === 0) {
    return (
      <div className="text-center text-muted py-4">
        {tval('no-records', 'No records found.')}
      </div>
    );
  }

  // --- Spatial layout ---
  if (hasCoords && spatialData) {
    const { items, minX, minY, rangeX, rangeY } = spatialData;
    const PADDING = 20;

    const scaleX = (CANVAS_W - PADDING * 2) / rangeX;
    const scaleY = (CANVAS_H - PADDING * 2) / rangeY;
    // Use uniform scale so shapes aren't distorted
    const scale  = Math.min(scaleX, scaleY, 6); // cap at 6 px/cm to avoid huge canvas

    const canvasW = Math.round(rangeX * scale) + PADDING * 2;
    const canvasH = Math.round(rangeY * scale) + PADDING * 2;

    return (
      <div>
        {/* Ruler hint */}
        <div className="text-muted small mb-2">
          {rangeX}×{rangeY} cm — {records.length} {tval('grid-places', 'places')}
        </div>

        <div style={{ overflowX: 'auto', overflowY: 'auto' }}>
          <div
            style={{
              position:   'relative',
              width:       canvasW,
              height:      canvasH,
              background:  '#f0f4e8',
              border:      '2px solid #c8d8a0',
              borderRadius: '6px',
              flexShrink:   0,
            }}
          >
            {items.map(({ record, x, y, w, h }) => {
              const px = Math.round((x - minX) * scale) + PADDING;
              const py = Math.round((y - minY) * scale) + PADDING;
              const pw = Math.max(Math.round(w * scale), 24);
              const ph = Math.max(Math.round(h * scale), 24);

              const colorValue = colorField ? record.data[colorField] : null;

              return (
                <div
                  key={record.id}
                  style={{ position: 'absolute', left: px, top: py, width: pw, height: ph }}
                >
                  <GridCell
                    record={record}
                    cellW={pw}
                    cellH={ph}
                    labelField={labelField}
                    colorValue={colorValue}
                    spacing={spacingField}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    interactions={config?.interactions}
                    viewAs={viewAs}
                    getRoleRank={getRoleRank}
                    onInteraction={onInteraction}
                    t={t}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // --- Flow layout (no coordinates) ---
  return (
    <div>
      <div className="text-muted small mb-2">
        {records.length} {tval('grid-places', 'places')}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {records.map((record) => {
          const colorValue = colorField ? record.data[colorField] : null;
          return (
            <GridCell
              key={record.id}
              record={record}
              cellW={CELL_SIZE}
              cellH={CELL_SIZE}
              labelField={labelField}
              colorValue={colorValue}
              spacing={spacingField}
              onEdit={onEdit}
              onDelete={onDelete}
              interactions={config?.interactions}
              viewAs={viewAs}
              getRoleRank={getRoleRank}
              onInteraction={onInteraction}
              t={t}
            />
          );
        })}
      </div>
    </div>
  );
};

export default GridDisplay;
