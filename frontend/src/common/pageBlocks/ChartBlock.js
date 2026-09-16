// SCOPE_composed_pages.md §3 / §6 — a grouped aggregate, drawn.
//
// **Charts are the exception that costs no new dependency.** `recharts` has
// been declared in both `frontend/package.json` and `base/frontend/package.json`
// since the initial commit (974ec23) and imported by nothing in either `src/`.
// Verified present in both built images (3.8.0) before this file was written,
// because a declaration nothing imports is exactly the one an image rebuild may
// quietly have dropped.
//
// Like `StatBlock`, this does no arithmetic: the rows arrive already aggregated
// over the block's own list queryset (§5), so the chart cannot plot a row the
// list would not have shown. And it keeps the same rule about emptiness —
// **a chart with no data says so, rather than drawing empty axes**, which read
// as "all values are zero".
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { toNumber } from './formatNumber';

// A brand-neutral sequence. Deliberately not the Bootstrap semantic colours:
// red and green mean "bad" and "good" to a reader, and a category that lands on
// one of them acquires a meaning nobody assigned it.
const SERIES_COLOURS = [
  '#4c6ef5', '#12b886', '#f59f00', '#e8590c', '#7048e8',
  '#1098ad', '#d6336c', '#5c940d', '#495057', '#9c36b5',
];

const ChartBlock = ({ rows, blockConfig = {}, t }) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);

  // A renderer must tolerate what it is handed — `TagsField`'s rule, and the
  // reason app 8's options-less select crashed on `options.find`.
  const data = (Array.isArray(rows) ? rows : [])
    .map((row) => ({
      label: String((row && row.label) ?? ''),
      value: toNumber(row && row.value),
    }))
    .filter((row) => row.value !== null);

  if (!data.length) {
    return (
      <p className="page-block-empty">
        {tval('page-chart-no-data', 'Nothing to chart yet.')}
      </p>
    );
  }

  const type = blockConfig.chart_type || 'bar';

  return (
    <ResponsiveContainer width="100%" height="100%" minHeight={120}>
      {type === 'pie' ? (
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="label" outerRadius="80%">
            {data.map((row, index) => (
              <Cell key={row.label} fill={SERIES_COLOURS[index % SERIES_COLOURS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      ) : type === 'line' ? (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke={SERIES_COLOURS[0]} dot={false} />
        </LineChart>
      ) : (
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill={SERIES_COLOURS[0]} />
        </BarChart>
      )}
    </ResponsiveContainer>
  );
};

export default ChartBlock;
