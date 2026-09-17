// SCOPE_composed_pages.md §4.1 — the page selection context, derived.
//
// **In `common/`, beside the renderers, for their reason.** It is pure — no
// DOM, no transport, no React — so both hosts can run the one copy, and one
// copy cannot drift from itself. It started under `generator/components/
// sandbox/`, which base cannot see, and the cost was exact: the emitted page
// had no selection at all, so `PAGE_BLOCKS` being a module constant left
// `block.scopeFk` undefined on every render, a subscriber scoped to nothing
// showed every record, and an `action` block — whose whole subject is the
// selected record — had no case in the emitted switch and answered "This block
// cannot be displayed."
//
// The owner's word was *plugins*. This is the read half of the answer, and it
// invents nothing: a block publishes the id of whatever the viewer picked, and
// a block that declares `filters_by` + `filter_fk` scopes itself to it by
// sending `fe_<filter_fk>=<id>` — the same filter `browse_by` already drives,
// and the same `scopeFk` prop the emitted container has taken since the base
// interactive embeds landed.
//
// Pure, no DOM, no transport: `entityLayout.js` / `embeddedScope.js`'s
// convention, so the derivation can be unit-tested without rendering anything.
//
// Selection itself is React state in `PageView`, keyed by block id. There is no
// endpoint and no persistence — **a selection is a thing the viewer is doing,
// not a thing the application stores** — which is also why `Page` has no
// per-viewer layout (§14).

/** Blocks that publish a selection other blocks may subscribe to. */
export function publishesSelection(block) {
  return ['entity_list', 'browse', 'map'].includes(block.kind);
}

/**
 * The query parameters a block should send with its own list request.
 *
 * `{}` when the block scopes nothing. A block that subscribes but whose source
 * has selected nothing yet returns `null` — see `isAwaitingSelection`, because
 * "no filter" and "a filter that is not satisfied yet" must not look the same:
 * sending no filter would show every record, which is the opposite of what the
 * owner composed.
 */
export function blockParams(block, selection = {}) {
  if (!block.filters_by || !block.filter_fk) return {};
  const selected = selection[block.filters_by];
  if (selected === undefined || selected === null || selected === '') return null;
  return { [`fe_${block.filter_fk}`]: selected };
}

/**
 * The same derivation as `blockParams`, in the shape a *generated* application
 * needs it: the `scopeFk` prop the emitted container has taken since the base
 * interactive embeds landed (`{field, fkKey, value}`), which it turns into the
 * same `fe_<fk>` filter. `fkKey` is that contract's third member and is inert
 * on a page, where the block is read-only — it is what the container prefills
 * with when something creates a child under a parent row, which a page never
 * does.
 *
 * Two hosts, one rule about what a block is scoped to; they differ only in how
 * they ask, which is the whole of the `routeSnappers` split.
 */
export function blockScopeFk(block, selection = {}) {
  const params = blockParams(block, selection);
  if (!params || !block.filter_fk) return undefined;
  return {
    field:  block.filter_fk,
    fkKey:  `${block.filter_fk}_id`,
    value:  selection[block.filters_by],
  };
}

/** True when the block is scoped to a selection nobody has made yet. */
export function isAwaitingSelection(block, selection = {}) {
  return blockParams(block, selection) === null;
}

/**
 * An `action` block's source record: the id it will act on.
 *
 * It subscribes by RECORD rather than through a column (`BLOCK_SPECS`'
 * `subscribes: 'record'`) — a button has no list to scope, so asking which
 * column joins a button to a row is a question with no answer.
 */
export function actionSourceId(block, selection = {}) {
  if (block.kind !== 'action' || !block.filters_by) return null;
  const selected = selection[block.filters_by];
  return selected === undefined || selected === '' ? null : selected;
}

/**
 * Record a pick, and drop every selection that was downstream of it.
 *
 * Changing A's selection makes B's stale: B was showing the rows of the OLD A,
 * and a stale id would scope C to a row that is no longer on screen. Cheaper
 * and more honest to clear than to guess what the viewer meant.
 */
export function selectRecord(selection, blocks, blockId, recordId) {
  const next = { ...selection };
  if (recordId === null || recordId === undefined || recordId === '') {
    delete next[blockId];
  } else {
    next[blockId] = recordId;
  }
  dependentsOf(blocks, blockId).forEach((id) => { delete next[id]; });
  return next;
}

/** Every block downstream of `blockId`, transitively. */
export function dependentsOf(blocks, blockId) {
  const out = [];
  const queue = [blockId];
  const seen = new Set([blockId]);
  while (queue.length) {
    const current = queue.shift();
    (blocks || []).forEach((block) => {
      if (block.filters_by !== current || seen.has(block.id)) return;
      seen.add(block.id);
      out.push(block.id);
      queue.push(block.id);
    });
  }
  return out;
}

/**
 * A one-line explanation for a block that is waiting, naming the block it is
 * waiting on — never a bare empty rectangle. A page is a grid of promises, and
 * an unexplained empty cell is indistinguishable from a cell whose data is
 * genuinely empty.
 */
export function awaitingLabel(block, blocks, t) {
  const source = (blocks || []).find((b) => b.id === block.filters_by);
  const name = (source && (source.title || source.entity)) || '';
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);
  return name
    ? tval('page-block-awaiting-named', `Pick a record in ${name} to see this.`)
    : tval('page-block-awaiting', 'Nothing selected yet.');
}
