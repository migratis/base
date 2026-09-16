// How a number reaches a page block's surface.
//
// It tolerates a number sent as a string, which is not defensiveness: prod app
// 6 stored `"197.8"` in a `decimal` column for every row an agent seeded, and
// `1 * "175.5"` is string repetition rather than a `TypeError`, so the guard
// written to catch exactly that never fired and the aggregate over it answered
// "unknown" forever. `computed.as_number` is the backend half of this reading;
// this is the same tolerance one layer out, because those rows are in
// production and a renderer must tolerate what it is handed.
//
// What it does NOT do is invent a number. A value with no reading as one comes
// back untouched, so a wrong value is visible as itself rather than as a
// plausible-looking 0.

export function toNumber(value) {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value !== 'string') return null;
  const text = value.trim();
  // Deliberately stricter than `Number()`, which reads '', 'Infinity' and
  // '0x10' — none of which a caller meant.
  if (!/^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/.test(text)) return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}

export function formatNumber(value, locale) {
  const n = toNumber(value);
  if (n === null) return String(value);
  // Whole numbers read as whole numbers; a rate keeps two places. Anything
  // more precise than that is a measurement, not a headline figure.
  const fractionDigits = Number.isInteger(n) ? 0 : 2;
  try {
    return n.toLocaleString(locale, {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    });
  } catch (e) {
    return String(n);
  }
}
