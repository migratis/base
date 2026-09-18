// SCOPE_composed_pages.md@87901d3 §6 — where a block sits, computed once.
//
// **The runtime needs no dragging.** A published page is plain CSS grid:
// `grid-column: <x+1> / span <w>; grid-row: <y+1> / span <h>`. That is this
// file, it lives in `common/` so the sandbox and every generated application
// are literally running the same copy, and it is the whole layout engine.
//
// It is also what the *composer* renders through, which is the reason D2 chose
// pointer maths over `react-grid-layout`. A library owns its own layout engine
// and compacts vertically as you drag; the shipped page does not compact at
// all. Two engines that must agree is the shape this repo has already paid for
// twice — four lists each enumerating display modes, and codegen's seven-entry
// copy of a ten-entry map. Here the composer computes `{x, y, w, h}` from
// pointer positions and then draws the result with the function below, so the
// preview and the shipped page cannot disagree about placement: they are the
// same function.

export const GRID_COLUMNS = 12;

// One row unit. A `stat` block is 1 unit tall, a list is 3-4.
export const ROW_HEIGHT_PX = 80;
export const GRID_GAP_PX = 16;

// Bootstrap's `md`. Below it the 12 columns collapse to one and blocks stack by
// `order` — a 4-column-wide chart on a 400px phone is unreadable, and the
// responsive rule is about the generated application too.
export const COLLAPSE_WIDTH_PX = 768;

export function isCollapsed(viewportWidth) {
  return Number(viewportWidth) > 0 && Number(viewportWidth) < COLLAPSE_WIDTH_PX;
}

/**
 * The CSS the grid container needs.
 *
 * @param {{collapsed?: boolean, rowHeight?: number, gap?: number}} [options]
 */
export function gridStyle(options = {}) {
  const { collapsed = false, rowHeight = ROW_HEIGHT_PX, gap = GRID_GAP_PX } = options;
  return {
    display: 'grid',
    gridTemplateColumns: collapsed ? '1fr' : `repeat(${GRID_COLUMNS}, 1fr)`,
    gridAutoRows: collapsed ? 'auto' : `${rowHeight}px`,
    gap: `${gap}px`,
    alignItems: 'stretch',
  };
}

/**
 * Where one block sits. Collapsed, every block is full width and placed by the
 * document order the caller established with `sortForCollapse` — explicit
 * placement is dropped rather than translated, because a 1-column grid has no
 * column to place into and a stale `gridRow` would leave holes.
 *
 * @param {{x: number, y: number, w: number, h: number}} block
 * @param {{collapsed?: boolean}} [options]
 */
export function blockStyle(block, options = {}) {
  const { collapsed = false } = options;
  if (collapsed) return { gridColumn: '1 / -1' };

  const x = clampInt(block && block.x, 0, GRID_COLUMNS - 1, 0);
  const y = clampInt(block && block.y, 0, Number.MAX_SAFE_INTEGER, 0);
  const w = clampInt(block && block.w, 1, GRID_COLUMNS - x, 1);
  const h = clampInt(block && block.h, 1, Number.MAX_SAFE_INTEGER, 1);
  return {
    gridColumn: `${x + 1} / span ${w}`,
    gridRow: `${y + 1} / span ${h}`,
  };
}

/**
 * Reading order for the collapsed grid: `order` first, then the position on the
 * wide grid, so a page that never set `order` still stacks the way it reads —
 * top to bottom, left to right.
 */
export function sortForCollapse(blocks) {
  return [...(blocks || [])].sort((a, b) => (
    (a.order || 0) - (b.order || 0)
    || (a.y || 0) - (b.y || 0)
    || (a.x || 0) - (b.x || 0)
    || (a.id || 0) - (b.id || 0)
  ));
}

/** Do two blocks claim a cell in common? The same predicate the backend's
 *  `page_block_overlap` advisory uses, so the composer can refuse to create
 *  what the advisory would report. */
export function overlaps(a, b) {
  return (
    a.x < b.x + b.w && b.x < a.x + a.w
    && a.y < b.y + b.h && b.y < a.y + a.h
  );
}

/** The number of grid rows a layout occupies — what the composer needs to know
 *  how tall to draw the canvas, including a spare row to drop into. */
export function gridRowCount(blocks) {
  return (blocks || []).reduce(
    (deepest, b) => Math.max(deepest, (b.y || 0) + (b.h || 1)), 0,
  );
}

function clampInt(value, minimum, maximum, fallback) {
  const n = Math.trunc(Number(value));
  if (!Number.isFinite(n)) return fallback;
  return Math.min(Math.max(n, minimum), maximum);
}
