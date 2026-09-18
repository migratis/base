// SCOPE_composed_pages.md@87901d3 §3 / §5 — one aggregated number.
//
// The number is computed server-side, **over the block's own list queryset**,
// and arrives here as a prop. That is the export scope's argument transferred:
// the aggregate runs through the same queryset builder the list uses, so field
// masking, row visibility, owner scope, persona identity and the read-role
// floor all apply with nothing re-implemented, and a stat can never count a row
// its list would not have shown.
//
// This component therefore does no arithmetic at all. It has one job the
// backend cannot do for it, and it is the important one:
//
//   **`null` is unknown, and unknown is not zero.**
//
// `computed.py`'s rule, in a renderer. An unknown number written as 0 is a
// wrong number that looks like an answer, and a dashboard is exactly the
// surface where nobody can tell the difference. `count` over nothing is
// genuinely 0 and the backend sends 0; every other op over nothing sends null.
import { formatNumber } from './formatNumber';

const StatBlock = ({ aggregate, blockConfig = {}, t }) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);
  const known = aggregate !== null && aggregate !== undefined && aggregate !== '';

  return (
    <div className="page-block-stat">
      <span className="page-block-stat-value">
        {known ? formatNumber(aggregate) : tval('page-stat-unknown', '—')}
      </span>
      {known && blockConfig.unit
        ? <span className="page-block-stat-unit">{blockConfig.unit}</span>
        : null}
    </div>
  );
};

export default StatBlock;
