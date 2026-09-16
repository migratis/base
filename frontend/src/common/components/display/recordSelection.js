// SCOPE_composed_pages.md §4.1 — when a click on a record selects it.
//
// One rule, one place. Every display below `SandboxList` receives
// `onSelectRecord`, and before this only `HubDetailDisplay` ever called it — so
// a composed page block scoped to a table waited forever for a selection that
// could not arrive, with the composition perfectly valid and nothing wrong to
// look at. Nine components each deciding what a click means is how that
// happens; a rule spelled out nine times can only be right in nine places at
// once.
//
//   **A click selects when the host asked for a selection and the click has no
//   other job.**
//
// The second half is what makes this safe to add to components the entity tabs
// already render. A click already means *edit* in `GridDisplay`,
// `KanbanDisplay` and `CalendarDisplay`, and *expand a detail panel* in
// `CardsDisplay` and `GalleryDisplay`. Where the viewer can edit, it goes on
// meaning that and nothing changes for anybody. A page block passes no
// `onEdit` — §4.2, the write path on a page is a workflow step and never an
// inline edit — so there the click is free, and it selects.
//
// `HubDetailDisplay` is deliberately untouched: it shows ONE record and already
// renders an explicit picker, which is a better affordance than a click and was
// the only one that ever worked.

const SELECTED_STYLE = {
  outline: '2px solid var(--bs-primary, #0d6efd)',
  outlineOffset: '-2px',
  background: 'rgba(13, 110, 253, 0.06)',
};

/**
 * @param {object} record  the record the row/card is rendering
 * @param {object} options {onSelectRecord, selectedRecordId, onEdit}
 * @returns {{selectable, selected, onClick, className, style, ariaSelected}}
 */
export function recordSelection(record, options = {}) {
  const { onSelectRecord, selectedRecordId = null, onEdit } = options;
  const id = record ? record.id : undefined;

  // `id == null` guards the one thing worse than not selecting: publishing
  // `undefined` as a selection, which reads downstream as "a record is picked"
  // and scopes a block to nothing.
  const selectable = typeof onSelectRecord === 'function' && !onEdit && id != null;
  const selected = selectable && selectedRecordId === id;

  return {
    selectable,
    selected,
    onClick: selectable ? () => onSelectRecord(id) : undefined,
    className: selected ? 'is-record-selected' : '',
    // Inline rather than a stylesheet rule: these components are mirrored into
    // base by the sync hook and rendered by every generated application, so the
    // highlight has to travel with the component rather than with a class that
    // may or may not be in the deployment's SCSS.
    style: selectable
      ? { cursor: 'pointer', ...(selected ? SELECTED_STYLE : {}) }
      : undefined,
    ariaSelected: selectable ? selected : undefined,
  };
}

export default recordSelection;
