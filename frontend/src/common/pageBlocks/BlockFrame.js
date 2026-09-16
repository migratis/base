// SCOPE_composed_pages.md §3.1 — the frame every page block is drawn in.
//
// In `common/` on purpose: the display-sync hook mirrors this directory into
// base, so the sandbox and every generated application render the *same file*.
// For `display_mode` the parity rail is structural because codegen keeps no map
// and dispatches through base's own `getDisplayMode`; for `page_block` it is
// structural because only one copy of each renderer exists.
//
// The constraint that comes with living here: **`common/` never imports a
// feature module**, so a block renderer takes its data as props and fetches
// nothing. The host fetches — `PageView` on one side, the emitted page
// component on the other — and the two differ in exactly one thing, the
// transport.
//
// The frame also owns the failure case, and owns it out loud: a block that
// cannot render says why, because **a blank rectangle is the one thing a
// composed page must never show.** A page is a grid of promises; an empty cell
// with no explanation is indistinguishable from a cell whose data is genuinely
// empty.
import { Component } from 'react';
import { blockStyle } from './pageGrid';

class BlockErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    // The host decides what to do with it — the sandbox reports it as a
    // warning, a generated application logs it. The frame's job is only to
    // keep one bad block from taking the page down with it.
    if (this.props.onError) this.props.onError(error);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="page-block-failed">
        {this.props.fallback}
      </div>
    );
  }
}

/**
 * @param {object}   block     {id, kind, title, x, y, w, h}
 * @param {boolean}  collapsed the grid has collapsed to one column
 * @param {string}   reason    why this block cannot render, if it cannot
 * @param {function} t         translator; every string here is a key
 */
const BlockFrame = ({
  block, collapsed = false, reason = '', onError, t, children,
}) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);
  const heading = block && block.title;

  return (
    <section
      className={`page-block page-block-${block ? block.kind : 'unknown'}`}
      style={blockStyle(block, { collapsed })}
      aria-label={heading || undefined}
    >
      {heading ? <h3 className="page-block-title">{heading}</h3> : null}
      <div className="page-block-body">
        {reason ? (
          <p className="page-block-unavailable">{reason}</p>
        ) : (
          <BlockErrorBoundary
            onError={onError}
            fallback={tval('page-block-render-failed',
              'This block could not be displayed.')}
          >
            {children}
          </BlockErrorBoundary>
        )}
      </div>
    </section>
  );
};

export default BlockFrame;
