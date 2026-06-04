import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Stage, Layer, Rect, Text, Line, Circle, Group, Ellipse } from 'react-konva';
import Form from 'react-bootstrap/Form';
import { toast } from 'react-toastify';
import SandboxService from '../../../services/sandbox.service';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CANVAS_MAX_W = 860;
const CANVAS_MAX_H = 560;
const MIN_DRAW_PX  = 8;
const PLACE_BG     = '#cfe0bb';
const RH_SIZE      = 10;

// Spacing is always entered in cm; convert to the canvas's native linear unit
const CM_TO_NATIVE = {
  nm2: 1e7, um2: 1e4, mm2: 10, cm2: 1, dm2: 0.1,
  m2: 0.01, dam2: 0.001, hm2: 1e-4, km2: 1e-5,
};

const SCALE_LINEAR_LABEL = {
  nm2: 'nm', um2: 'μm', mm2: 'mm', cm2: 'cm', dm2: 'dm',
  m2: 'm', dam2: 'dam', hm2: 'hm', km2: 'km',
};

const AREA_LABEL = {
  nm2: 'nm²', um2: 'μm²', mm2: 'mm²', cm2: 'cm²', dm2: 'dm²',
  m2: 'm²', dam2: 'dam²', hm2: 'hm²', km2: 'km²',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const toNum = (v) => { const n = parseFloat(v); return isNaN(n) ? null : n; };

const PALETTE = ['#66bb6a','#42a5f5','#ffa726','#ef5350','#ab47bc','#26c6da','#8d6e63','#78909c'];

const luminance = (hex) => {
  try {
    const h = hex.replace('#', '');
    const r = parseInt(h.slice(0,2),16), g = parseInt(h.slice(2,4),16), b = parseInt(h.slice(4,6),16);
    return (r*299 + g*587 + b*114) / 1000;
  } catch { return 0; }
};
const textOn = (hex) => luminance(hex) > 128 ? '#1a1a1a' : '#ffffff';

const detectField = (fields, candidates) => {
  for (const c of candidates) if (fields.find(f => f.name === c)) return c;
  return '';
};


const rectsOverlap = (ax, ay, aw, ah, bx, by, bw, bh) =>
  ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by;

// Auto grid step: target ~5 divisions across the shorter axis
const autoGridStep = (sz) => {
  const t = sz / 5;
  if (t <= 0) return 1;
  const mag = Math.pow(10, Math.floor(Math.log10(t)));
  const n = t / mag;
  return n < 2 ? mag : n < 5 ? 2 * mag : 5 * mag;
};

// ---------------------------------------------------------------------------
// GridCanvas
// ---------------------------------------------------------------------------

const GridCanvas = ({
  token, entity, config = {}, t,
  onRequestCreate, onRequestEdit, onDelete, refreshKey = 0,
}) => {
  const opts   = config?.display_mode_options || {};
  const fields = entity?.fields || [];

  // --- Field resolution ---
  const xField       = opts.grid_x_field     || detectField(fields, ['x','col','pos_x','position_x','left']);
  const yField       = opts.grid_y_field     || detectField(fields, ['y','row','pos_y','position_y','top']);
  const wField       = opts.grid_width_field || detectField(fields, ['width','w','size_x']);
  const hField       = opts.grid_height_field|| detectField(fields, ['height','h','size_y']);
  const labelField   = opts.grid_label_field || detectField(fields, ['name','title','label']);
  const spacingField = opts.grid_spacing_field || detectField(fields, ['spacing','plant_spacing','distance','interval']);

  // If the entity has no explicit x/y position fields, look for a JSON geometry field
  // that stores {x, y, w, h} (e.g. Place.geometry).
  const geometryField = (!xField && !yField)
    ? detectField(fields, ['geometry','geom','spatial','shape_data','coordinates'])
    : '';

  // Field that stores the computed area (auto-set from w×h)
  const areaField = detectField(fields, ['area_sqm','area','superficie','area_m2','surface_m2']);

  // Container entity (e.g. Season — provides the item filter)
  const containerEntity      = opts.grid_container_entity       || '';
  const containerFkField     = opts.grid_container_fk_field     || '';
  const containerWidthField  = opts.grid_container_width_field  || '';
  const containerHeightField = opts.grid_container_height_field || '';
  const containerScaleField  = opts.grid_container_scale_field  || 'scale';

  // Ancestor canvas entity (e.g. Garden — its ShapeField defines the canvas boundary)
  const canvasAncestorEntity     = opts.grid_canvas_entity      || '';
  const canvasAncestorFkField    = opts.grid_canvas_fk_field    || '';
  const canvasAncestorShapeField = opts.grid_canvas_shape_field || '';

  // Fill entity (e.g. Plant)
  const fillEntity     = opts.grid_fill_entity      || '';
  const fillLabelField = opts.grid_fill_label_field || '';

  const fillFkField = useMemo(() => {
    if (opts.grid_fill_fk_field) return opts.grid_fill_fk_field;
    if (!fillEntity) return '';
    const rel = (entity.relationships || []).find(r =>
      r.related_entity?.toLowerCase() === fillEntity.toLowerCase()
    );
    return rel?.field_name || '';
  }, [opts.grid_fill_fk_field, fillEntity, entity.relationships]);

  // --- Data state ---
  const [containerRecords, setContainerRecords]     = useState([]);
  const [containerOptions, setContainerOptions]     = useState([]); // {value, label} for select
  const [selectedContainerId, setSelectedContainerId] = useState(null);
  const [canvasAncestorRecord, setCanvasAncestorRecord] = useState(null);
  const [placeRecords, setPlaceRecords] = useState([]);
  const [fillMap, setFillMap]           = useState({});
  const [loading, setLoading]           = useState(true);

  const fillColorField = useMemo(() => {
    const configured = opts.grid_fill_color_field || '';
    const sample = Object.values(fillMap)[0];
    if (!sample) return configured;
    if (configured && typeof sample.data?.[configured] === 'string'
        && /^#[0-9a-f]{3,6}$/i.test(sample.data[configured])) return configured;
    const entry = Object.entries(sample.data || {}).find(
      ([, v]) => typeof v === 'string' && /^#[0-9a-f]{6}$/i.test(v)
    );
    return entry?.[0] || configured;
  }, [opts.grid_fill_color_field, fillMap]);

  // --- Interaction state ---
  const [drawing, setDrawing]     = useState(null);
  const [hoveredId, setHoveredId] = useState(null);
  const [popover, setPopover]     = useState(null);

  // Render hovered entity last so its resize handle is always on top of siblings.
  const sortedPlaceRecords = useMemo(() => {
    if (!hoveredId) return placeRecords;
    const idx = placeRecords.findIndex(r => r.id === hoveredId);
    if (idx === -1) return placeRecords;
    const copy = [...placeRecords];
    copy.push(copy.splice(idx, 1)[0]);
    return copy;
  }, [placeRecords, hoveredId]);
  const isDrawingRef    = useRef(false);
  const stageRef        = useRef(null);
  const placeRecordsRef = useRef(placeRecords);
  useEffect(() => { placeRecordsRef.current = placeRecords; }, [placeRecords]);

  const canvasOverlayRef      = useRef(null);
  const canvasOverlayLabelRef = useRef(null);
  const placeResizePreviewRef = useRef(null);
  const placeResizeDimRef     = useRef(null);

  // --- Parse ancestor ShapeField for canvas dimensions + shape type ---
  const _parseShapeField = (value) => {
    if (!value) return null;
    try {
      const p = typeof value === 'string' ? JSON.parse(value) : value;
      const a = toNum(p.a), b = toNum(p.b);
      return a > 0 && b > 0 ? { w: a, h: b, scale: p.scale || 'm2', shape: p.shape || 'rectangle' } : null;
    } catch { return null; }
  };

  const selectedContainer = containerRecords.find(r => r.id === selectedContainerId);

  const _ancestorShape = canvasAncestorRecord && canvasAncestorShapeField
    ? _parseShapeField(canvasAncestorRecord.data?.[canvasAncestorShapeField])
    : null;

  // Canvas dimensions: ancestor (Garden) shape is always the primary source.
  // Container (Season) width/height fields are only used as fallback when no ancestor is configured.
  const canvasW = _ancestorShape?.w
    || (containerWidthField && toNum(selectedContainer?.data?.[containerWidthField]))
    || 400;
  const canvasH = _ancestorShape?.h
    || (containerHeightField && toNum(selectedContainer?.data?.[containerHeightField]))
    || 300;
  const areaUnit = _ancestorShape?.scale
    || selectedContainer?.data?.[containerScaleField]
    || 'm2';
  const canvasShape = _ancestorShape?.shape || 'rectangle';
  const linearUnit  = SCALE_LINEAR_LABEL[areaUnit] || '';

  // Scale: pixels per native unit — bounded by canvas max size
  const scale  = Math.min(CANVAS_MAX_W / canvasW, CANVAS_MAX_H / canvasH);
  const stageW = Math.round(canvasW * scale);
  const stageH = Math.round(canvasH * scale);

  const gridStep = useMemo(() => autoGridStep(Math.min(canvasW, canvasH)), [canvasW, canvasH]);
  // Minimum place size: 2% of the shorter canvas dimension
  const minPlace = useMemo(() => Math.max(0.001, Math.min(canvasW, canvasH) * 0.02), [canvasW, canvasH]);

  // --- Editable canvas dimensions ---
  const [dimInput, setDimInput] = useState({ w: '', h: '' });
  useEffect(() => { setDimInput({ w: String(canvasW), h: String(canvasH) }); }, [canvasW, canvasH]);

  const saveDim = useCallback((newW, newH) => {
    const w = Math.max(0.001, toNum(newW) || canvasW);
    const h = Math.max(0.001, toNum(newH) || canvasH);
    if (canvasAncestorRecord && canvasAncestorShapeField) {
      const raw = canvasAncestorRecord.data?.[canvasAncestorShapeField];
      let parsed = {};
      try { parsed = typeof raw === 'string' ? JSON.parse(raw) : (raw || {}); } catch { /**/ }
      const updated = JSON.stringify({ ...parsed, a: w, b: h, surface: w * h });
      const updatedData = { ...canvasAncestorRecord.data, [canvasAncestorShapeField]: updated };
      SandboxService.sandboxUpdate(token, canvasAncestorEntity, { ...updatedData, id: canvasAncestorRecord.id });
      setCanvasAncestorRecord(prev => ({ ...prev, data: updatedData }));
    } else if (selectedContainer && containerWidthField && containerHeightField) {
      SandboxService.sandboxUpdate(token, containerEntity, {
        ...selectedContainer.data, [containerWidthField]: w, [containerHeightField]: h,
        id: selectedContainer.id,
      });
      setContainerRecords(prev => prev.map(r =>
        r.id === selectedContainer.id
          ? { ...r, data: { ...r.data, [containerWidthField]: w, [containerHeightField]: h } }
          : r
      ));
    }
  }, [selectedContainer, containerEntity, containerWidthField, containerHeightField,
      canvasAncestorRecord, canvasAncestorEntity, canvasAncestorShapeField, canvasW, canvasH, token]);

  // --- Item geometry helpers ---

  // Parse item position and size from geometry JSON or separate fields (native units)
  const parseItemGeom = useCallback((record) => {
    const defW = canvasW * 0.2, defH = canvasH * 0.2;
    if (geometryField) {
      const raw = record.data?.[geometryField];
      try {
        const g = raw ? JSON.parse(raw) : {};
        return {
          x: toNum(g.x) ?? 0, y: toNum(g.y) ?? 0,
          w: toNum(g.w) ?? defW, h: toNum(g.h) ?? defH,
        };
      } catch { return { x: 0, y: 0, w: defW, h: defH }; }
    }
    return {
      x: toNum(record.data[xField]) ?? 0, y: toNum(record.data[yField]) ?? 0,
      w: toNum(record.data[wField]) ?? defW, h: toNum(record.data[hField]) ?? defH,
    };
  }, [geometryField, xField, yField, wField, hField, canvasW, canvasH]);

  // Build updated record.data reflecting new position/size
  const buildItemData = useCallback((record, { x, y, w, h }) => {
    const rx = Math.round(x * 1000) / 1000, ry = Math.round(y * 1000) / 1000;
    const rw = Math.round(w * 1000) / 1000, rh = Math.round(h * 1000) / 1000;
    if (geometryField) {
      const raw = record.data?.[geometryField];
      let g = {};
      try { g = JSON.parse(raw || '{}'); } catch { /**/ }
      const newGeom = JSON.stringify({ ...g, x: rx, y: ry, w: rw, h: rh });
      const updated = { ...record.data, [geometryField]: newGeom };
      if (areaField) updated[areaField] = parseFloat((rw * rh).toFixed(6));
      return updated;
    }
    const updated = { ...record.data };
    if (xField) updated[xField] = rx;
    if (yField) updated[yField] = ry;
    if (wField) updated[wField] = rw;
    if (hField) updated[hField] = rh;
    if (areaField) updated[areaField] = parseFloat((rw * rh).toFixed(6));
    return updated;
  }, [geometryField, xField, yField, wField, hField, areaField]);

  // --- Data fetching ---
  useEffect(() => {
    if (!containerEntity) return;
    Promise.all([
      SandboxService.sandboxList(token, containerEntity, 1),
      SandboxService.sandboxOptions(token, containerEntity),
    ]).then(([listData, optData]) => {
      const records = listData?.items || [];
      setContainerRecords(records);
      setContainerOptions(optData?.options || []);
      setSelectedContainerId(prev => prev ?? (records[0]?.id || null));
    });
  }, [token, containerEntity, refreshKey]);

  // When selected Season changes → load the linked Garden record
  useEffect(() => {
    if (!canvasAncestorEntity || !canvasAncestorShapeField) return;
    const containerRecord = containerRecords.find(r => r.id === selectedContainerId);
    if (!containerRecord) { setCanvasAncestorRecord(null); return; }
    if (!canvasAncestorFkField) { setCanvasAncestorRecord(containerRecord); return; }
    const ancestorId = containerRecord.data?.[canvasAncestorFkField];
    if (!ancestorId) { setCanvasAncestorRecord(null); return; }
    SandboxService.sandboxGet(token, canvasAncestorEntity, ancestorId)
      .then(record => setCanvasAncestorRecord(record || null))
      .catch(() => setCanvasAncestorRecord(null));
  }, [token, canvasAncestorEntity, canvasAncestorFkField, canvasAncestorShapeField,
      containerRecords, selectedContainerId]);

  useEffect(() => {
    if (!fillEntity) return;
    const loadAll = async () => {
      const map = {};
      let page = 1;
      while (true) {
        const data = await SandboxService.sandboxList(token, fillEntity, page);
        (data?.items || []).forEach(r => { map[r.id] = r; });
        if (page >= (data?.pages || 1)) break;
        page++;
      }
      setFillMap(map);
    };
    loadAll();
  }, [token, fillEntity, refreshKey]);

  useEffect(() => {
    const filters = {};
    if (containerFkField && selectedContainerId) filters[`fe_${containerFkField}`] = selectedContainerId;
    setLoading(true);
    SandboxService.sandboxList(token, entity.name, 1, '', 'asc', filters)
      .then(data => setPlaceRecords(data?.items || []))
      .finally(() => setLoading(false));
  }, [token, entity.name, containerFkField, selectedContainerId, refreshKey]);

  // --- Overlap check (in native units) ---
  const checkOverlap = useCallback((x, y, w, h, excludeId) =>
    placeRecordsRef.current.some(r => {
      if (r.id === excludeId) return false;
      const { x: rx, y: ry, w: rw, h: rh } = parseItemGeom(r);
      return rectsOverlap(x, y, w, h, rx, ry, rw, rh);
    }),
  [parseItemGeom]);

  // --- Cursor ---
  const setCursor = useCallback((cursor) => {
    if (stageRef.current) stageRef.current.container().style.cursor = cursor;
  }, []);

  // --- Draw-to-create handlers ---
  const handleStageMouseDown = useCallback((e) => {
    const onBg = e.target === e.target.getStage() || e.target.name() === 'canvas-bg';
    if (!onBg || !onRequestCreate) return;
    const pos = e.target.getStage().getPointerPosition();
    if (!pos) return;
    isDrawingRef.current = true;
    const sx = pos.x / scale, sy = pos.y / scale;
    setDrawing({ startX: sx, startY: sy, x: sx, y: sy, w: 0, h: 0 });
  }, [onRequestCreate, scale]);

  const handleStageMouseMove = useCallback((e) => {
    if (!isDrawingRef.current) return;
    const pos = e.target.getStage().getPointerPosition();
    if (!pos) return;
    const cx = pos.x / scale, cy = pos.y / scale;
    setDrawing(d => !d ? null : ({
      ...d,
      x: Math.min(d.startX, cx), y: Math.min(d.startY, cy),
      w: Math.abs(cx - d.startX), h: Math.abs(cy - d.startY),
    }));
  }, [scale]);

  // Form field overrides: hide geometry/position fields and computed area
  const gridFormOverrides = useMemo(() => {
    const overrides = {};
    [xField, yField, wField, hField, geometryField, areaField].filter(Boolean).forEach(f => {
      overrides[f] = { visible: false };
    });
    (opts.grid_hidden_fields || []).forEach(f => { if (f) overrides[f] = { visible: false }; });
    (config.calculated_fields || []).forEach(f => { if (f) overrides[f] = { visible: false }; });
    if (spacingField) overrides[spacingField] = { help_text: 'Espacement entre plantes (cm)' };
    return overrides;
  }, [xField, yField, wField, hField, geometryField, areaField, spacingField,
      opts.grid_hidden_fields, config.calculated_fields]);

  const handleStageMouseUp = useCallback(() => {
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;
    setDrawing(d => {
      if (!d) return null;
      const { x, y, w, h } = d;
      if (w * scale < MIN_DRAW_PX || h * scale < MIN_DRAW_PX) return null;
      if (checkOverlap(x, y, w, h, null)) return null;
      const presetData = buildItemData({ data: {} }, { x, y, w, h });
      if (containerFkField && selectedContainerId) presetData[containerFkField] = selectedContainerId;
      onRequestCreate(presetData, gridFormOverrides);
      return null;
    });
  }, [scale, checkOverlap, buildItemData, containerFkField, selectedContainerId, onRequestCreate, gridFormOverrides]);

  // --- Drag end ---
  const handleDragEnd = useCallback((e, record) => {
    const { x: origX, y: origY, w, h } = parseItemGeom(record);
    const newX = Math.max(0, Math.min(canvasW - w, e.target.x() / scale));
    const newY = Math.max(0, Math.min(canvasH - h, e.target.y() / scale));
    const bgRect = e.target.findOne('.bg-rect');
    if (bgRect) { bgRect.stroke('rgba(0,0,0,0.3)'); bgRect.strokeWidth(1); }
    if (checkOverlap(newX, newY, w, h, record.id)) {
      e.target.position({ x: origX * scale, y: origY * scale });
      e.target.getLayer().batchDraw();
      return;
    }
    const updatedData = buildItemData(record, { x: newX, y: newY, w, h });
    setPlaceRecords(prev => prev.map(r => r.id === record.id ? { ...r, data: updatedData } : r));
    SandboxService.sandboxUpdate(token, entity.name, { ...updatedData, id: record.id });
  }, [scale, canvasW, canvasH, parseItemGeom, buildItemData, checkOverlap, token, entity.name]);

  // --- Resolution helpers ---
  const resolveDotColor = useCallback((record) => {
    if (!fillFkField) return '#2e7d32';
    const fill = fillMap[record.data[fillFkField]];
    const raw = fillColorField ? fill?.data?.[fillColorField] : null;
    if (!fill) return '#2e7d32';
    if (raw && /^#[0-9a-f]{3,6}$/i.test(String(raw))) return raw;
    return PALETTE[1 + ((Math.abs(fill.id) - 1) % (PALETTE.length - 1))];
  }, [fillFkField, fillColorField, fillMap]);

  const resolveLabel = useCallback((record) => {
    if (labelField && record.data[labelField]) return String(record.data[labelField]);
    if (fillFkField && fillLabelField) {
      const fill = fillMap[record.data[fillFkField]];
      if (fill?.data?.[fillLabelField]) return String(fill.data[fillLabelField]);
    }
    return '';
  }, [labelField, fillFkField, fillLabelField, fillMap]);

  const formatArea = useCallback((w, h) => {
    const a = w * h;
    const label = AREA_LABEL[areaUnit] || '';
    const fmt = a < 0.01 ? a.toExponential(3) : a % 1 === 0 ? a.toString() : parseFloat(a.toFixed(4)).toString();
    return `${fmt} ${label}`;
  }, [areaUnit]);

  // Plant dots — spacing entered in cm, converted to native canvas units
  const computeDots = useCallback((record) => {
    const hasFill = fillFkField && record.data[fillFkField];
    if (!hasFill) return [];
    const rawSpacing = spacingField ? (toNum(record.data[spacingField]) || 0) : 0;
    const factor = CM_TO_NATIVE[areaUnit] ?? 1;
    const spacingNative = rawSpacing > 0 ? rawSpacing * factor : gridStep * 0.3;
    const { w, h } = parseItemGeom(record);
    if (spacingNative <= 0 || !w || !h) return [];
    const cols = Math.max(1, Math.ceil(w / spacingNative));
    const rows = Math.max(1, Math.ceil(h / spacingNative));
    const startX = cols === 1 ? w / 2 : (w - (cols - 1) * spacingNative) / 2;
    const startY = rows === 1 ? h / 2 : (h - (rows - 1) * spacingNative) / 2;
    const dots = [];
    for (let row = 0; row < rows && dots.length < 800; row++)
      for (let col = 0; col < cols && dots.length < 800; col++)
        dots.push({
          cx: (startX + col * spacingNative) * scale,
          cy: (startY + row * spacingNative) * scale,
        });
    return dots;
  }, [spacingField, areaUnit, gridStep, parseItemGeom, scale, fillFkField]);

  // --- Grid lines ---
  const gridLines = useMemo(() => {
    const lines = [];
    for (let x = 0; x <= canvasW + gridStep; x += gridStep)
      lines.push(<Line key={`v${x}`} points={[x*scale,0,x*scale,stageH]} stroke="#c8e6c9" strokeWidth={0.5} listening={false} />);
    for (let y = 0; y <= canvasH + gridStep; y += gridStep)
      lines.push(<Line key={`h${y}`} points={[0,y*scale,stageW,y*scale]} stroke="#c8e6c9" strokeWidth={0.5} listening={false} />);
    return lines;
  }, [canvasW, canvasH, gridStep, scale, stageW, stageH]);

  // Canvas boundary shape overlay (shows circle/triangle boundary if ancestor is not rectangle)
  const canvasShapeOverlay = useMemo(() => {
    if (canvasShape === 'circle') {
      return (
        <Ellipse
          x={stageW / 2} y={stageH / 2}
          radiusX={stageW / 2 - 1} radiusY={stageH / 2 - 1}
          stroke="#6a9b4f" strokeWidth={3}
          fill="transparent" dash={[10, 5]} listening={false}
        />
      );
    }
    if (canvasShape === 'triangle') {
      return (
        <Line
          points={[0, stageH, stageW, stageH, 0, 0]}
          stroke="#6a9b4f" strokeWidth={3}
          closed fill="transparent" dash={[10, 5]} listening={false}
        />
      );
    }
    return null;
  }, [canvasShape, stageW, stageH]);

  // --- Canvas resize overlay (HTML, not Konva) ---
  const updateCanvasOverlay = useCallback((pxW, pxH) => {
    const nw = Math.round(pxW / scale * 100) / 100;
    const nh = Math.round(pxH / scale * 100) / 100;
    if (canvasOverlayRef.current) {
      Object.assign(canvasOverlayRef.current.style, { width: `${pxW}px`, height: `${pxH}px`, display: 'block' });
    }
    if (canvasOverlayLabelRef.current) {
      Object.assign(canvasOverlayLabelRef.current.style, {
        left: `${Math.max(4, pxW - 130)}px`, top: `${Math.max(4, pxH - 22)}px`, display: 'block',
      });
      canvasOverlayLabelRef.current.textContent = `${nw} × ${nh} ${linearUnit}`;
    }
  }, [scale, linearUnit]);

  const hideCanvasOverlay = useCallback(() => {
    if (canvasOverlayRef.current)      canvasOverlayRef.current.style.display      = 'none';
    if (canvasOverlayLabelRef.current) canvasOverlayLabelRef.current.style.display = 'none';
  }, []);

  const showPlaceResizePreview = useCallback((px, py, pxW, pxH) => {
    const nw = Math.round(pxW / scale * 100) / 100;
    const nh = Math.round(pxH / scale * 100) / 100;
    if (placeResizePreviewRef.current) {
      placeResizePreviewRef.current.x(px); placeResizePreviewRef.current.y(py);
      placeResizePreviewRef.current.width(pxW); placeResizePreviewRef.current.height(pxH);
      placeResizePreviewRef.current.visible(true);
    }
    if (placeResizeDimRef.current) {
      placeResizeDimRef.current.text(`${nw} × ${nh} ${linearUnit}`);
      placeResizeDimRef.current.x(px + pxW + 4); placeResizeDimRef.current.y(py + pxH - 10);
      placeResizeDimRef.current.visible(true);
    }
    placeResizePreviewRef.current?.getLayer()?.batchDraw();
  }, [scale, linearUnit]);

  const hidePlaceResizePreview = useCallback(() => {
    if (placeResizePreviewRef.current) placeResizePreviewRef.current.visible(false);
    if (placeResizeDimRef.current)     placeResizeDimRef.current.visible(false);
    placeResizePreviewRef.current?.getLayer()?.batchDraw();
  }, []);

  // --- Render ---
  if (loading) return (
    <div className="text-center py-5"><div className="spinner-border spinner-border-sm text-secondary" /></div>
  );

  const drawInvalid = drawing && drawing.w > 0 && checkOverlap(drawing.x, drawing.y, drawing.w, drawing.h, null);
  const canResize   = Boolean(
    (containerEntity && selectedContainer && containerWidthField && containerHeightField) ||
    (canvasAncestorRecord && canvasAncestorShapeField)
  );

  return (
    <div>
      {/* Container selector */}
      {containerRecords.length > 1 && (
        <div className="d-flex align-items-center gap-2 mb-2">
          <span className="text-muted small">{opts.grid_container_label || containerEntity}:</span>
          <Form.Select size="sm" style={{ maxWidth: 220 }} value={selectedContainerId ?? ''}
            onChange={e => setSelectedContainerId(parseInt(e.target.value))}>
            {containerRecords.map(r => {
              const opt = containerOptions.find(o => o.value === r.id);
              return (
                <option key={r.id} value={r.id}>
                  {opt?.label || `#${r.id}`}
                </option>
              );
            })}
          </Form.Select>
        </div>
      )}

      {/* Toolbar */}
      <div className="text-muted small mb-2 d-flex align-items-center gap-2 flex-wrap">
        {canResize ? (
          <>
            <span>W:</span>
            <input type="number" min="0.001" step="any" value={dimInput.w}
              onChange={e => setDimInput(d => ({ ...d, w: e.target.value }))}
              onBlur={() => saveDim(dimInput.w, dimInput.h)}
              onKeyDown={e => { if (e.key === 'Enter') e.target.blur(); }}
              style={{ width: 72, fontSize: 12, padding: '1px 4px', border: '1px solid #ccc', borderRadius: 3 }}
            />
            <span>H:</span>
            <input type="number" min="0.001" step="any" value={dimInput.h}
              onChange={e => setDimInput(d => ({ ...d, h: e.target.value }))}
              onBlur={() => saveDim(dimInput.w, dimInput.h)}
              onKeyDown={e => { if (e.key === 'Enter') e.target.blur(); }}
              style={{ width: 72, fontSize: 12, padding: '1px 4px', border: '1px solid #ccc', borderRadius: 3 }}
            />
            <span>{linearUnit}</span>
            <span>·</span>
          </>
        ) : (
          <><span>{canvasW}×{canvasH} {linearUnit}</span><span>·</span></>
        )}
        <span>Surface: {formatArea(canvasW, canvasH)}</span>
        {spacingField && <><span>·</span><span>Espacement en cm</span></>}
        <span>·</span>
        <span>Dessiner · Déplacer · Redimensionner ↘</span>
      </div>

      <div style={{ overflowX: 'auto', overflowY: 'auto' }}>
        <div style={{ position: 'relative', display: 'inline-block' }}>

          {/* Info popover */}
          {popover && (
            <div style={{
              position: 'absolute', left: popover.x + 14, top: Math.max(4, popover.y - 36),
              background: '#fff', border: '1px solid #b0c9e0', borderRadius: 5,
              padding: '5px 10px', fontSize: 12, lineHeight: 1.6,
              zIndex: 30, pointerEvents: 'none',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)', whiteSpace: 'nowrap',
            }}>
              {popover.surface && <div><strong>Surface :</strong> {popover.surface}</div>}
              {popover.hasPlants && <div><strong>Plantes :</strong> {popover.count}</div>}
            </div>
          )}

          {/* Canvas resize HTML overlay */}
          <div ref={canvasOverlayRef} style={{
            position: 'absolute', top: 0, left: 0, display: 'none',
            pointerEvents: 'none', zIndex: 10,
            border: '2px dashed #1565c0', borderRadius: 4, boxSizing: 'border-box',
          }} />
          <div ref={canvasOverlayLabelRef} style={{
            position: 'absolute', display: 'none', pointerEvents: 'none', zIndex: 11,
            fontSize: 11, fontWeight: 'bold', color: '#1565c0',
            background: 'rgba(255,255,255,0.85)', padding: '1px 5px', borderRadius: 3,
          }} />

          <Stage
            ref={stageRef}
            width={stageW} height={stageH}
            onMouseDown={handleStageMouseDown}
            onMouseMove={handleStageMouseMove}
            onMouseUp={handleStageMouseUp}
            onMouseLeave={() => { isDrawingRef.current = false; setDrawing(null); setCursor('crosshair'); }}
            style={{ cursor: 'crosshair' }}
          >
            <Layer>
              {/* Canvas background */}
              <Rect
                name="canvas-bg"
                x={0} y={0} width={stageW} height={stageH}
                fill="#eef5e8" stroke="#a5c880" strokeWidth={2} cornerRadius={4}
              />

              {/* Grid lines */}
              {gridLines}

              {/* Garden shape outline (circle / triangle) */}
              {canvasShapeOverlay}

              {/* Scale ruler */}
              <Line points={[8,stageH-8, 8+gridStep*scale,stageH-8]} stroke="#888" strokeWidth={1} listening={false} />
              <Line points={[8,stageH-12, 8,stageH-4]} stroke="#888" strokeWidth={1} listening={false} />
              <Line points={[8+gridStep*scale,stageH-12, 8+gridStep*scale,stageH-4]} stroke="#888" strokeWidth={1} listening={false} />
              <Text x={8} y={stageH-22} width={gridStep*scale}
                text={`${gridStep} ${linearUnit}`} align="center" fontSize={9} fill="#666" listening={false} />

              {/* Place rectangles */}
              {sortedPlaceRecords.map(record => {
                const { x: ix, y: iy, w: iw, h: ih } = parseItemGeom(record);
                const px  = ix * scale;
                const py  = iy * scale;
                const rw  = Math.max(iw * scale, 4);
                const rh  = Math.max(ih * scale, 4);
                const dotClr   = resolveDotColor(record);
                const label    = resolveLabel(record);
                const dots     = computeDots(record);
                const isHov    = hoveredId === record.id;
                const areaText = formatArea(iw, ih);
                const hasDots  = dots.length > 0;
                const fg       = textOn(PLACE_BG);
                const dotR     = Math.min(Math.max(1, rw / 14), 5);
                const fontSize = Math.max(8, Math.min(13, rw / 5, rh / 2.5));

                return (
                  <Group
                    key={record.id}
                    x={px} y={py}
                    draggable
                    dragBoundFunc={pos => ({
                      x: Math.max(0, Math.min(stageW - rw, pos.x)),
                      y: Math.max(0, Math.min(stageH - rh, pos.y)),
                    })}
                    onDragStart={() => { setCursor('grabbing'); setHoveredId(null); }}
                    onDragMove={e => {
                      const nx = e.target.x() / scale, ny = e.target.y() / scale;
                      const overlapping = checkOverlap(nx, ny, iw, ih, record.id);
                      const bgR = e.target.findOne('.bg-rect');
                      if (bgR) { bgR.stroke(overlapping ? '#c62828' : '#1565c0'); bgR.strokeWidth(2.5); e.target.getLayer().batchDraw(); }
                    }}
                    onDragEnd={e => { setCursor('crosshair'); handleDragEnd(e, record); }}
                    onMouseEnter={e => {
                      if (isDrawingRef.current) return;
                      setHoveredId(record.id);
                      e.target.getStage().container().style.cursor = 'grab';
                    }}
                    onMouseLeave={e => {
                      setHoveredId(null);
                      if (!isDrawingRef.current) e.target.getStage().container().style.cursor = 'crosshair';
                    }}
                  >
                    <Rect
                      name="bg-rect"
                      width={rw} height={rh}
                      fill={PLACE_BG}
                      stroke={isHov ? '#1565c0' : 'rgba(0,0,0,0.3)'}
                      strokeWidth={isHov ? 2.5 : 1}
                      cornerRadius={3}
                    />

                    {/* Plant dots */}
                    {hasDots && (
                      <Group clipX={0} clipY={0} clipWidth={rw} clipHeight={rh} listening={false}>
                        {dots.map((dot, i) => (
                          <Circle key={i}
                            x={dot.cx} y={dot.cy} radius={dotR}
                            fill={dotClr} stroke="#fff"
                            strokeWidth={Math.max(0.8, dotR * 0.25)} opacity={0.92}
                          />
                        ))}
                      </Group>
                    )}

                    {/* Label */}
                    {label && fontSize > 5 && rw > 20 && rh > 12 && (
                      <Text text={label} width={rw} height={rh}
                        align="center" verticalAlign="middle"
                        fontSize={fontSize} fontStyle="bold" fill={fg} listening={false} />
                    )}

                    {/* ℹ info */}
                    {rw > 16 && rh > 16 && (
                      <Group x={3} y={rh - 15}
                        onMouseEnter={e => {
                          e.cancelBubble = true;
                          const ptr = e.target.getStage().getPointerPosition();
                          setPopover({ x: ptr.x, y: ptr.y, surface: areaText, count: dots.length, hasPlants: hasDots });
                          e.target.getStage().container().style.cursor = 'default';
                        }}
                        onMouseLeave={e => {
                          setPopover(null);
                          if (!isDrawingRef.current) e.target.getStage().container().style.cursor = isHov ? 'grab' : 'crosshair';
                        }}
                      >
                        <Rect width={12} height={12} fill="transparent" />
                        <Circle x={6} y={6} radius={6} fill="rgba(21,101,192,0.72)" listening={false} />
                        <Text text="i" width={12} height={12} align="center" verticalAlign="middle"
                          fontSize={9} fontStyle="bold" fill="#fff" listening={false} />
                      </Group>
                    )}

                    {/* Hover actions */}
                    {isHov && rh >= 20 && (
                      <>
                        {onRequestEdit && rw >= 36 && (
                          <Group x={rw - 36} y={2}
                            onMouseDown={e => { e.cancelBubble = true; }}
                            onClick={e => { e.cancelBubble = true; onRequestEdit(record, gridFormOverrides); }}
                            onMouseEnter={e => { e.cancelBubble = true; e.target.getStage().container().style.cursor = 'pointer'; }}
                            onMouseLeave={e => { e.target.getStage().container().style.cursor = 'grab'; }}
                          >
                            <Rect width={16} height={16} fill="rgba(21,101,192,0.85)" cornerRadius={3} />
                            <Text text="⚙" width={16} height={16} align="center" verticalAlign="middle" fontSize={11} fill="#fff" listening={false} />
                          </Group>
                        )}
                        {onDelete && rw >= 18 && (
                          <Group x={rw - 18} y={2}
                            onMouseDown={e => { e.cancelBubble = true; }}
                            onClick={e => {
                              e.cancelBubble = true;
                              if (!window.confirm(t ? t('confirm-delete') : 'Confirmer la suppression ?')) return;
                              SandboxService.sandboxDelete(token, entity.name, record.id).then(() => {
                                setPlaceRecords(prev => prev.filter(r => r.id !== record.id));
                                setHoveredId(null);
                                toast.success(t ? t('successfully-deleted') : 'Supprimé');
                              });
                            }}
                            onMouseEnter={e => { e.cancelBubble = true; e.target.getStage().container().style.cursor = 'pointer'; }}
                            onMouseLeave={e => { e.target.getStage().container().style.cursor = 'grab'; }}
                          >
                            <Rect width={16} height={16} fill="rgba(180,30,30,0.85)" cornerRadius={3} />
                            <Text text="✕" width={16} height={16} align="center" verticalAlign="middle" fontSize={11} fill="#fff" listening={false} />
                          </Group>
                        )}
                      </>
                    )}

                    {/* Place resize handle — bottom-right */}
                    {isHov && rw >= 14 && rh >= 14 && (
                      <Group
                        x={rw - RH_SIZE} y={rh - RH_SIZE}
                        draggable
                        dragBoundFunc={pos => ({
                          x: Math.max(px + minPlace * scale - RH_SIZE, Math.min(stageW - RH_SIZE, pos.x)),
                          y: Math.max(py + minPlace * scale - RH_SIZE, Math.min(stageH - RH_SIZE, pos.y)),
                        })}
                        onMouseDown={e => { e.cancelBubble = true; }}
                        onDragStart={e => { e.cancelBubble = true; showPlaceResizePreview(px, py, rw, rh); }}
                        onDragMove={e => {
                          e.cancelBubble = true;
                          showPlaceResizePreview(
                            e.target.getParent().x(), e.target.getParent().y(),
                            Math.max(minPlace * scale, e.target.x() + RH_SIZE),
                            Math.max(minPlace * scale, e.target.y() + RH_SIZE),
                          );
                        }}
                        onDragEnd={e => {
                          e.cancelBubble = true;
                          hidePlaceResizePreview();
                          const newW = Math.max(minPlace, (e.target.x() + RH_SIZE) / scale);
                          const newH = Math.max(minPlace, (e.target.y() + RH_SIZE) / scale);
                          if (checkOverlap(ix, iy, newW, newH, record.id)) {
                            e.target.position({ x: rw - RH_SIZE, y: rh - RH_SIZE });
                            e.target.getLayer().batchDraw();
                            return;
                          }
                          const updatedData = buildItemData(record, { x: ix, y: iy, w: newW, h: newH });
                          setPlaceRecords(prev => prev.map(r => r.id === record.id ? { ...r, data: updatedData } : r));
                          SandboxService.sandboxUpdate(token, entity.name, { ...updatedData, id: record.id });
                        }}
                        onMouseEnter={e => { e.cancelBubble = true; e.target.getStage().container().style.cursor = 'nwse-resize'; }}
                        onMouseLeave={e => { e.target.getStage().container().style.cursor = 'grab'; }}
                      >
                        <Rect width={RH_SIZE} height={RH_SIZE} fill="#1565c0" cornerRadius={2} />
                      </Group>
                    )}
                  </Group>
                );
              })}

              {/* Canvas resize handle */}
              {canResize && (
                <Group
                  x={stageW - 14} y={stageH - 14}
                  draggable
                  dragBoundFunc={pos => ({ x: Math.max(26, pos.x), y: Math.max(26, pos.y) })}
                  onDragStart={() => updateCanvasOverlay(stageW, stageH)}
                  onDragMove={e => updateCanvasOverlay(e.target.x() + 14, e.target.y() + 14)}
                  onDragEnd={e => {
                    hideCanvasOverlay();
                    const newW = (e.target.x() + 14) / scale;
                    const newH = (e.target.y() + 14) / scale;
                    e.target.position({ x: stageW - 14, y: stageH - 14 });
                    e.target.getLayer().batchDraw();
                    saveDim(newW, newH);
                  }}
                  onMouseEnter={e => { e.target.getStage().container().style.cursor = 'nwse-resize'; }}
                  onMouseLeave={e => { e.target.getStage().container().style.cursor = 'crosshair'; }}
                >
                  <Rect width={14} height={14} fill="#a5c880" stroke="#6a9b4f" strokeWidth={1} cornerRadius={2} />
                  <Text text="⤡" width={14} height={14} align="center" verticalAlign="middle" fontSize={9} fill="#fff" listening={false} />
                </Group>
              )}

              {/* Place resize preview */}
              <Rect ref={placeResizePreviewRef}
                x={0} y={0} width={0} height={0}
                fill="transparent" stroke="#1565c0" strokeWidth={2}
                dash={[6,3]} cornerRadius={3} listening={false} visible={false}
              />
              <Text ref={placeResizeDimRef}
                text="" x={0} y={0} fontSize={10} fill="#1565c0" fontStyle="bold"
                listening={false} visible={false}
              />

              {/* Drawing preview */}
              {drawing && drawing.w * scale > 1 && drawing.h * scale > 1 && (
                <Rect
                  x={drawing.x * scale} y={drawing.y * scale}
                  width={drawing.w * scale} height={drawing.h * scale}
                  fill={drawInvalid ? 'rgba(198,40,40,0.12)' : 'rgba(21,101,192,0.12)'}
                  stroke={drawInvalid ? '#c62828' : '#1565c0'}
                  strokeWidth={2} dash={[6,3]} listening={false}
                />
              )}
              {drawing && drawing.w * scale > MIN_DRAW_PX && drawing.h * scale > MIN_DRAW_PX && (
                <Text
                  x={drawing.x * scale} y={drawing.y * scale + drawing.h * scale / 2 - 7}
                  width={drawing.w * scale}
                  text={`${Math.round(drawing.w*100)/100}×${Math.round(drawing.h*100)/100} ${linearUnit}`}
                  align="center" fontSize={11}
                  fill={drawInvalid ? '#c62828' : '#1565c0'} listening={false}
                />
              )}
            </Layer>
          </Stage>
        </div>
      </div>
    </div>
  );
};

export default GridCanvas;
