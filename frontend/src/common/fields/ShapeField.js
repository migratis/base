import { useRef, useEffect, useMemo, useCallback, useState } from 'react';
import { useFormContext, useController } from 'react-hook-form';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';

// ---------------------------------------------------------------------------
// Scale definitions
// ---------------------------------------------------------------------------
const SCALES = [
  { value: 'nm2',  label: 'nm²',  linear: 'nm'  },
  { value: 'um2',  label: 'μm²',  linear: 'μm'  },
  { value: 'mm2',  label: 'mm²',  linear: 'mm'  },
  { value: 'cm2',  label: 'cm²',  linear: 'cm'  },
  { value: 'dm2',  label: 'dm²',  linear: 'dm'  },
  { value: 'm2',   label: 'm²',   linear: 'm'   },
  { value: 'dam2', label: 'dam²', linear: 'dam' },
  { value: 'hm2',  label: 'hm²',  linear: 'hm'  },
  { value: 'km2',  label: 'km²',  linear: 'km'  },
];

const SHAPES = [
  { value: 'rectangle', icon: '▬', title: 'Rectangle' },
  { value: 'circle',    icon: '●', title: 'Circle'    },
  { value: 'triangle',  icon: '▲', title: 'Triangle'  },
];

// ---------------------------------------------------------------------------
// Surface calculation
// ---------------------------------------------------------------------------
function calcSurface(shape, a, b) {
  const fa = parseFloat(a) || 0;
  const fb = parseFloat(b) || 0;
  switch (shape) {
    case 'rectangle': return Math.round(fa * fb);
    case 'circle':    return Math.round(Math.PI * fa * fa);
    case 'triangle':  return Math.round(0.5 * fa * fb);
    default:          return 0;
  }
}

function formatSurface(surface, scaleValue) {
  const scale = SCALES.find(s => s.value === scaleValue) || SCALES[5];
  const n = parseFloat(surface) || 0;
  if (n === 0) return `0 ${scale.label}`;
  return `${n % 1 === 0 ? n : parseFloat(n.toFixed(2))} ${scale.label}`;
}

// ---------------------------------------------------------------------------
// Canvas constants
// ---------------------------------------------------------------------------
const CANVAS_W = 280;
const CANVAS_H = 160;
const PAD      = 20;
const DRAW_W   = CANVAS_W - PAD * 2;
const DRAW_H   = CANVAS_H - PAD * 2;
const HANDLE_R = 5;   // handle circle radius (px)
const HIT_R    = 9;   // hit-test radius (px)

// ---------------------------------------------------------------------------
// Drawn bounds — where the shape sits on the canvas (canvas pixel coords)
// ---------------------------------------------------------------------------
function getDrawnBounds(shape, a, b) {
  const fa = parseFloat(a) || 0;
  const fb = parseFloat(b) || 0;
  if (fa <= 0) return null;

  if (shape === 'rectangle') {
    const ratio = fb > 0 ? fa / fb : 1;
    let rw, rh;
    if (ratio > DRAW_W / DRAW_H) { rw = DRAW_W; rh = DRAW_W / ratio; }
    else                          { rh = DRAW_H; rw = DRAW_H * ratio; }
    const rx = PAD + (DRAW_W - rw) / 2;
    const ry = PAD + (DRAW_H - rh) / 2;
    return { type: 'rectangle', rx, ry, rw, rh };
  }
  if (shape === 'circle') {
    const r = Math.min(DRAW_W, DRAW_H) / 2;
    return { type: 'circle', cx: CANVAS_W / 2, cy: CANVAS_H / 2, r };
  }
  if (shape === 'triangle') {
    const ratio = fb > 0 ? fa / fb : 1;
    let tw, th;
    if (ratio > DRAW_W / DRAW_H) { tw = DRAW_W; th = DRAW_W / ratio; }
    else                          { th = DRAW_H; tw = DRAW_H * ratio; }
    const tx = PAD + (DRAW_W - tw) / 2;
    const ty = PAD + (DRAW_H - th) / 2;
    return { type: 'triangle', tx, ty, tw, th };
  }
  return null;
}

// ---------------------------------------------------------------------------
// Handle positions (canvas pixel coords)
// ---------------------------------------------------------------------------
function getHandles(bounds) {
  if (!bounds) return [];
  if (bounds.type === 'rectangle') {
    const { rx, ry, rw, rh } = bounds;
    return [
      { id: 'e',  x: rx + rw,     y: ry + rh / 2, cursor: 'ew-resize',   sx: +1, sy:  0 },
      { id: 'w',  x: rx,          y: ry + rh / 2, cursor: 'ew-resize',   sx: -1, sy:  0 },
      { id: 's',  x: rx + rw / 2, y: ry + rh,     cursor: 'ns-resize',   sx:  0, sy: +1 },
      { id: 'n',  x: rx + rw / 2, y: ry,          cursor: 'ns-resize',   sx:  0, sy: -1 },
      { id: 'se', x: rx + rw,     y: ry + rh,     cursor: 'nwse-resize', sx: +1, sy: +1 },
      { id: 'sw', x: rx,          y: ry + rh,     cursor: 'nesw-resize', sx: -1, sy: +1 },
      { id: 'ne', x: rx + rw,     y: ry,          cursor: 'nesw-resize', sx: +1, sy: -1 },
      { id: 'nw', x: rx,          y: ry,          cursor: 'nwse-resize', sx: -1, sy: -1 },
    ];
  }
  if (bounds.type === 'circle') {
    const { cx, cy, r } = bounds;
    return [
      { id: 'ce', x: cx + r, y: cy,     cursor: 'ew-resize' },
      { id: 'cw', x: cx - r, y: cy,     cursor: 'ew-resize' },
      { id: 'cn', x: cx,     y: cy - r, cursor: 'ns-resize' },
      { id: 'cs', x: cx,     y: cy + r, cursor: 'ns-resize' },
    ];
  }
  if (bounds.type === 'triangle') {
    const { tx, ty, tw, th } = bounds;
    return [
      { id: 'tr', x: tx + tw, y: ty + th, cursor: 'ew-resize', sx: +1, sy:  0 },
      { id: 'tl', x: tx,      y: ty + th, cursor: 'ew-resize', sx: -1, sy:  0 },
      { id: 'ta', x: tx,      y: ty,      cursor: 'ns-resize', sx:  0, sy: -1 },
    ];
  }
  return [];
}

function hitTestHandle(handles, px, py) {
  for (const h of handles) {
    const d = Math.hypot(px - h.x, py - h.y);
    if (d <= HIT_R) return h;
  }
  return null;
}

// Compute new a/b from handle drag (uses starting values + frozen bounds for stability)
function applyHandleDrag(handle, curX, curY, dragState) {
  const { x0, y0, startA, startB, bounds } = dragState;
  const dx = curX - x0, dy = curY - y0;

  if (bounds.type === 'rectangle') {
    const { rw, rh } = bounds;
    const { sx = 0, sy = 0 } = handle;
    let newA = startA, newB = startB;
    if (sx !== 0 && rw > 0) newA = Math.max(1, Math.round(startA + sx * dx * 2 * startA / rw));
    if (sy !== 0 && rh > 0) newB = Math.max(1, Math.round(startB + sy * dy * 2 * startB / rh));
    return { a: newA, b: newB };
  }

  if (bounds.type === 'circle') {
    const { cx, cy, r } = bounds;
    const newDist = Math.hypot(curX - cx, curY - cy);
    const newA = Math.max(1, Math.round(startA * newDist / r));
    return { a: newA, b: startB };
  }

  if (bounds.type === 'triangle') {
    const { tw, th } = bounds;
    let newA = startA, newB = startB;
    const { sx = 0, sy = 0 } = handle;
    if (sx !== 0 && tw > 0) newA = Math.max(1, Math.round(startA + sx * dx * 2 * startA / tw));
    if (sy !== 0 && th > 0) newB = Math.max(1, Math.round(startB + sy * dy * 2 * startB / th));
    return { a: newA, b: newB };
  }

  return { a: startA, b: startB };
}

// ---------------------------------------------------------------------------
// Canvas rendering
// ---------------------------------------------------------------------------
function renderCanvas(canvas, shape, a, b, scaleLabel, {
  handles = [], hoveredHandleId = null,
  drag = null,          // { x0,y0,x1,y1 } for new draw preview
  previewA, previewB,   // live values during handle drag
} = {}) {
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
  ctx.fillStyle = '#f8f9fa';
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

  // Which values to render (preview overrides during drag)
  const fa = parseFloat(previewA !== undefined ? previewA : a) || 0;
  const fb = parseFloat(previewB !== undefined ? previewB : b) || 0;
  const isDragHandle = previewA !== undefined;

  // Draw the shape
  if (fa > 0) {
    ctx.fillStyle   = 'rgba(13,110,253,0.18)';
    ctx.strokeStyle = '#0d6efd';
    ctx.lineWidth   = 2;
    ctx.globalAlpha = drag ? 0.3 : 1;

    if (shape === 'rectangle') {
      const ratio = fb > 0 ? fa / fb : 1;
      let rw, rh;
      if (ratio > DRAW_W / DRAW_H) { rw = DRAW_W; rh = DRAW_W / ratio; }
      else                          { rh = DRAW_H; rw = DRAW_H * ratio; }
      const rx = PAD + (DRAW_W - rw) / 2, ry = PAD + (DRAW_H - rh) / 2;
      ctx.beginPath(); ctx.rect(rx, ry, rw, rh); ctx.fill(); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#0d6efd'; ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`${fa} ${scaleLabel}`, rx + rw / 2, ry - 5);
      ctx.save(); ctx.translate(rx - 5, ry + rh / 2); ctx.rotate(-Math.PI / 2);
      ctx.fillText(`${fb} ${scaleLabel}`, 0, 0); ctx.restore();

    } else if (shape === 'circle') {
      const r = Math.min(DRAW_W, DRAW_H) / 2;
      const cx = CANVAS_W / 2, cy = CANVAS_H / 2;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#0d6efd'; ctx.font = '11px sans-serif'; ctx.textAlign = 'center';
      ctx.fillText(`r = ${fa} ${scaleLabel}`, cx, cy + r + 14);

    } else if (shape === 'triangle') {
      const ratio = fb > 0 ? fa / fb : 1;
      let tw, th;
      if (ratio > DRAW_W / DRAW_H) { tw = DRAW_W; th = DRAW_W / ratio; }
      else                          { th = DRAW_H; tw = DRAW_H * ratio; }
      const tx = PAD + (DRAW_W - tw) / 2, ty = PAD + (DRAW_H - th) / 2;
      ctx.beginPath(); ctx.moveTo(tx, ty + th); ctx.lineTo(tx + tw, ty + th);
      ctx.lineTo(tx, ty); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#0d6efd'; ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`base = ${fa} ${scaleLabel}`, tx + tw / 2, ty + th + 14);
      ctx.textAlign = 'left';
      ctx.fillText(`h = ${fb} ${scaleLabel}`, tx - PAD + 2, ty + th / 2);
    }
    ctx.globalAlpha = 1;
  }

  // Draw resize handles
  if (handles.length > 0) {
    handles.forEach(h => {
      const hovered = h.id === hoveredHandleId;
      ctx.beginPath(); ctx.arc(h.x, h.y, HANDLE_R, 0, Math.PI * 2);
      ctx.fillStyle   = hovered ? '#0d6efd' : '#fff';
      ctx.strokeStyle = '#0d6efd';
      ctx.lineWidth   = 1.5;
      ctx.fill(); ctx.stroke();
    });
  }

  // Draw new-shape drag preview
  if (drag) {
    const px = Math.min(drag.x0, drag.x1), py = Math.min(drag.y0, drag.y1);
    const pw = Math.abs(drag.x1 - drag.x0), ph = Math.abs(drag.y1 - drag.y0);
    ctx.save();
    ctx.strokeStyle = '#0d6efd'; ctx.fillStyle = 'rgba(13,110,253,0.15)';
    ctx.lineWidth = 1.5; ctx.setLineDash([5, 3]);
    if (shape === 'rectangle') {
      ctx.beginPath(); ctx.rect(px, py, pw, ph); ctx.fill(); ctx.stroke();
    } else if (shape === 'circle') {
      const r = Math.max(pw, ph) / 2;
      ctx.beginPath(); ctx.arc(px + pw / 2, py + ph / 2, r, 0, Math.PI * 2);
      ctx.fill(); ctx.stroke();
    } else if (shape === 'triangle') {
      ctx.beginPath(); ctx.moveTo(px, py + ph); ctx.lineTo(px + pw, py + ph);
      ctx.lineTo(px, py); ctx.closePath(); ctx.fill(); ctx.stroke();
    }
    ctx.setLineDash([]);
    if (drag.previewA > 0) {
      ctx.fillStyle = '#0d6efd'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center';
      const txt = shape === 'circle'
        ? `r = ${drag.previewA} ${scaleLabel}`
        : `${drag.previewA} × ${drag.previewB} ${scaleLabel}`;
      ctx.fillText(txt, CANVAS_W / 2, CANVAS_H - 5);
    }
    ctx.restore();
  }

  // Hint when empty
  if (fa <= 0 && !drag) {
    ctx.fillStyle = '#adb5bd'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText('Drag to draw', CANVAS_W / 2, CANVAS_H / 2);
  }
}

// ---------------------------------------------------------------------------
// Viewport for new-shape drawing
// ---------------------------------------------------------------------------
function getViewportSize(shape, a, b) {
  const fa = parseFloat(a) || 0;
  const fb = shape === 'circle' ? fa : (parseFloat(b) || 0);
  return Math.max(fa, fb) > 0 ? Math.ceil(Math.max(fa, fb) * 2) : 100;
}

function newDrawPxToUnits(pxW, pxH, vpSize) {
  const uPerPx = vpSize / Math.min(DRAW_W, DRAW_H);
  return {
    a: Math.max(1, Math.round(Math.abs(pxW) * uPerPx)),
    b: Math.max(1, Math.round(Math.abs(pxH) * uPerPx)),
  };
}

// ---------------------------------------------------------------------------
// ShapeField component
// ---------------------------------------------------------------------------
const ShapeField = ({
  name,
  label,
  required     = false,
  help         = null,
  disabled     = false,
  defaultScale = 'm2',
}) => {
  const EMPTY = JSON.stringify({ shape: 'rectangle', a: '', b: '', scale: defaultScale, surface: 0 });
  const { control } = useFormContext();
  const { field } = useController({ name, control, defaultValue: EMPTY });

  const parsed = useMemo(() => {
    try {
      const v = typeof field.value === 'string' ? JSON.parse(field.value || EMPTY) : (field.value || {});
      return {
        shape:   v.shape   || 'rectangle',
        a:       v.a       !== undefined ? v.a       : '',
        b:       v.b       !== undefined ? v.b       : '',
        scale:   v.scale   || defaultScale,
        surface: v.surface || 0,
      };
    } catch {
      return { shape: 'rectangle', a: '', b: '', scale: defaultScale, surface: 0 };
    }
  }, [field.value, EMPTY, defaultScale]);

  const push = useCallback((updates) => {
    const next = { ...parsed, ...updates };
    if (next.a !== '') next.a = Math.round(parseFloat(next.a) || 0);
    if (next.b !== '') next.b = Math.round(parseFloat(next.b) || 0);
    next.surface = calcSurface(next.shape, next.a, next.b);
    field.onChange(JSON.stringify(next));
  }, [parsed, field]);

  const canvasRef        = useRef(null);
  const modeRef          = useRef('idle');   // 'idle' | 'drag_handle' | 'new_draw'
  const dragStateRef     = useRef(null);
  const [hoveredHandle, setHoveredHandle] = useState(null);

  const scaleLinear = (SCALES.find(s => s.value === parsed.scale) || SCALES[5]).linear;
  const hasShape    = parseFloat(parsed.a) > 0;

  // Stable redraw: called on every render and on hover change
  const redraw = useCallback((opts = {}) => {
    const bounds  = getDrawnBounds(parsed.shape, parsed.a, parsed.b);
    const handles = hasShape && !disabled ? getHandles(bounds) : [];
    renderCanvas(canvasRef.current, parsed.shape, parsed.a, parsed.b, scaleLinear, {
      handles,
      hoveredHandleId: opts.hoveredHandleId ?? hoveredHandle,
      ...opts,
    });
  }, [parsed.shape, parsed.a, parsed.b, scaleLinear, hasShape, disabled, hoveredHandle]);

  useEffect(() => {
    if (modeRef.current === 'idle') redraw();
  }, [redraw]);

  // Convert client coords to canvas pixel coords
  const toCanvas = useCallback((clientX, clientY) => {
    const rect = canvasRef.current.getBoundingClientRect();
    return {
      x: (clientX - rect.left) * (CANVAS_W / rect.width),
      y: (clientY - rect.top)  * (CANVAS_H / rect.height),
    };
  }, []);

  const handleMouseDown = useCallback((e) => {
    if (disabled) return;
    e.preventDefault();
    const { x, y } = toCanvas(e.clientX, e.clientY);

    if (hasShape) {
      // Try to grab a handle
      const bounds  = getDrawnBounds(parsed.shape, parsed.a, parsed.b);
      const handles = getHandles(bounds);
      const hit     = hitTestHandle(handles, x, y);
      if (hit) {
        modeRef.current = 'drag_handle';
        dragStateRef.current = {
          x0: x, y0: y,
          startA: parseFloat(parsed.a) || 0,
          startB: parseFloat(parsed.b) || 0,
          handle: hit,
          bounds,
        };
      }
      // Click inside shape but not on a handle → no action (shape exists, use handles)
    } else {
      // No shape yet → start fresh draw
      modeRef.current = 'new_draw';
      dragStateRef.current = { x0: x, y0: y };
    }
  }, [disabled, hasShape, parsed.shape, parsed.a, parsed.b, toCanvas]);

  const handleMouseMove = useCallback((e) => {
    const { x, y } = toCanvas(e.clientX, e.clientY);

    if (modeRef.current === 'drag_handle') {
      const ds = dragStateRef.current;
      const { a: newA, b: newB } = applyHandleDrag(ds.handle, x, y, ds);
      // Live canvas preview without updating form (avoids re-render storm)
      renderCanvas(canvasRef.current, parsed.shape, parsed.a, parsed.b, scaleLinear, {
        handles: [],
        previewA: newA,
        previewB: parsed.shape === 'circle' ? parsed.b : newB,
      });
      return;
    }

    if (modeRef.current === 'new_draw') {
      const { x0, y0 } = dragStateRef.current;
      const vpSize = getViewportSize(parsed.shape, parsed.a, parsed.b);
      const { a: pA, b: pB } = newDrawPxToUnits(x - x0, y - y0, vpSize);
      const pA2 = parsed.shape === 'circle' ? Math.max(pA, pB) : pA;
      renderCanvas(canvasRef.current, parsed.shape, parsed.a, parsed.b, scaleLinear, {
        handles: [],
        drag: { x0, y0, x1: x, y1: y, previewA: pA2, previewB: pB },
      });
      return;
    }

    // Idle: update cursor based on handle hover
    if (hasShape && !disabled) {
      const bounds  = getDrawnBounds(parsed.shape, parsed.a, parsed.b);
      const handles = getHandles(bounds);
      const hit     = hitTestHandle(handles, x, y);
      const hitId   = hit?.id || null;
      if (hitId !== hoveredHandle) {
        setHoveredHandle(hitId);
        canvasRef.current.style.cursor = hit ? hit.cursor : 'default';
        redraw({ hoveredHandleId: hitId });
      }
    }
  }, [toCanvas, parsed.shape, parsed.a, parsed.b, scaleLinear, hasShape, disabled, hoveredHandle, redraw]);

  const handleMouseUp = useCallback((e) => {
    const { x, y } = toCanvas(e.clientX, e.clientY);

    if (modeRef.current === 'drag_handle') {
      const ds = dragStateRef.current;
      const { a: newA, b: newB } = applyHandleDrag(ds.handle, x, y, ds);
      modeRef.current = 'idle';
      dragStateRef.current = null;
      push({ a: newA, b: parsed.shape === 'circle' ? parsed.b : newB });
      return;
    }

    if (modeRef.current === 'new_draw') {
      const { x0, y0 } = dragStateRef.current;
      modeRef.current = 'idle';
      dragStateRef.current = null;
      const dx = x - x0, dy = y - y0;
      if (Math.abs(dx) < 4 && Math.abs(dy) < 4) { redraw(); return; } // mis-click
      const vpSize = getViewportSize(parsed.shape, parsed.a, parsed.b);
      const { a, b } = newDrawPxToUnits(dx, dy, vpSize);
      push(parsed.shape === 'circle' ? { a: Math.max(a, b) } : { a, b });
      return;
    }
  }, [toCanvas, parsed.shape, parsed.b, push, redraw]);

  // Release outside canvas
  useEffect(() => {
    const onUp = (e) => {
      if (modeRef.current !== 'idle') handleMouseUp(e);
    };
    window.addEventListener('mouseup', onUp);
    return () => window.removeEventListener('mouseup', onUp);
  }, [handleMouseUp]);

  const isCircle = parsed.shape === 'circle';
  const aLabel   = parsed.shape === 'rectangle' ? 'W' : parsed.shape === 'triangle' ? 'Base' : 'Radius';
  const bLabel   = parsed.shape === 'rectangle' ? 'H' : 'Height';

  const hint = disabled ? null : hasShape
    ? 'Drag the handles to resize'
    : 'Drag on the canvas to draw · or enter dimensions below';

  return (
    <div className="migratis-field">
      {label && (
        <label className="form-label">
          {label}{required && <span style={{ color: 'red' }}>&nbsp;*</span>}
        </label>
      )}

      {/* Shape type selector */}
      <div className="d-flex gap-1 mb-2">
        {SHAPES.map(s => (
          <Button
            key={s.value}
            size="sm"
            variant={parsed.shape === s.value ? 'primary' : 'outline-secondary'}
            onClick={() => !disabled && push({ shape: s.value })}
            disabled={disabled}
            title={s.title}
            style={{ minWidth: 40, fontSize: '1rem' }}
          >
            {s.icon}
          </Button>
        ))}
        {hasShape && !disabled && (
          <Button
            size="sm"
            variant="outline-danger"
            onClick={() => push({ a: '', b: '', surface: 0 })}
            title="Reset shape"
            style={{ marginLeft: 'auto', fontSize: '0.75rem' }}
          >
            ✕ Reset
          </Button>
        )}
      </div>

      {/* Interactive canvas */}
      <canvas
        ref={canvasRef}
        width={CANVAS_W}
        height={CANVAS_H}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => {
          if (modeRef.current === 'idle' && hoveredHandle) {
            setHoveredHandle(null);
            if (canvasRef.current) canvasRef.current.style.cursor = 'default';
            redraw({ hoveredHandleId: null });
          }
        }}
        style={{
          border: '1px solid #dee2e6',
          borderRadius: 4,
          display: 'block',
          maxWidth: '100%',
          background: '#f8f9fa',
          cursor: disabled ? 'default' : hasShape ? 'default' : 'crosshair',
          userSelect: 'none',
        }}
      />
      {hint && (
        <small className="text-muted" style={{ fontSize: '0.75rem' }}>{hint}</small>
      )}

      {/* Dimension inputs */}
      <InputGroup className="mt-1" size="sm">
        <InputGroup.Text>{aLabel}</InputGroup.Text>
        <Form.Control
          type="number" min="0" step="1"
          value={parsed.a}
          onChange={e => !disabled && push({ a: e.target.value })}
          disabled={disabled} placeholder="0"
          style={{ maxWidth: 90 }}
        />
        {!isCircle && (
          <>
            <InputGroup.Text>{bLabel}</InputGroup.Text>
            <Form.Control
              type="number" min="0" step="1"
              value={parsed.b}
              onChange={e => !disabled && push({ b: e.target.value })}
              disabled={disabled} placeholder="0"
              style={{ maxWidth: 90 }}
            />
          </>
        )}
        <Form.Select
          value={parsed.scale}
          onChange={e => !disabled && push({ scale: e.target.value })}
          disabled={disabled} style={{ maxWidth: 90 }}
        >
          {SCALES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </Form.Select>
      </InputGroup>

      {parsed.surface > 0 && (
        <div className="mt-1 text-muted" style={{ fontSize: '0.85rem' }}>
          Surface&nbsp;=&nbsp;<strong>{formatSurface(parsed.surface, parsed.scale)}</strong>
        </div>
      )}
      {help && <small className="form-text text-muted">{help}</small>}
    </div>
  );
};

export default ShapeField;
