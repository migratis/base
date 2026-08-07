import { IoLocationOutline as GeoIcon } from 'react-icons/io5';
import { geoSummary } from './geoSummary';

// The read-only rendering of a `geo` value on a text surface — one shared
// component so the row displays (table / list / cards, in the sandbox AND in a
// generated app, which imports the same files) cannot drift into three
// different readings of the same geometry. See geoSummary.js for why this is
// text and not a map.

const GeoValue = ({ value, t, empty = '—' }) => {
  const summary = geoSummary(value);
  if (!summary) return empty;
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);
  return (
    <span className="d-inline-flex align-items-center gap-1" title={summary.type}>
      <GeoIcon aria-hidden="true" />
      {summary.text || `${summary.count} ${tval('geo-points', 'points')}`}
    </span>
  );
};

export default GeoValue;
