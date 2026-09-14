/**
 * What a candidate LOOKS like before anyone picks it.
 *
 * The lookup control asks one thing of a user — *choose one of these* — and for
 * as long as it existed it showed one line per candidate: the label the source
 * answered with, and a button. On OMDb that is "Blade Runner" above "Blade
 * Runner 2049": two rows a user can only tell apart by picking one, reading
 * what landed in the form, and undoing it. Every value was already resolved by
 * the time the list rendered (`services.search` runs both mapper hops before it
 * answers); the row simply did not show any of them.
 *
 * Pure, and deliberately so — no React, no `t`, no DOM. It decides what a row
 * SAYS; `LookupControl` decides how it looks. That is `datasource/mapping.py`'s
 * split one layer up, and it is what lets the interesting judgements be tested
 * without rendering anything.
 *
 * Two rails, both already this module's:
 *
 *   - **the target field's DECLARED type decides**, never the shape of the
 *     value. A `string` field holding `https://…/br.jpg` is a URL and renders
 *     as text; only a field declared `image` becomes a picture. That is exactly
 *     `services.inline_media_values`' rule, and for the same reason: guessing
 *     from the value is how a reference code `"007"` becomes a number.
 *   - **a row never claims to fill more than it will.** The count is intersected
 *     with the host's `fillable`, so an edit form that lets a suggestion write
 *     one field says one, not eleven.
 */

// How many facts one row shows. A result list is scanned, not read: past about
// four lines the rows stop being comparable at a glance, which is the whole
// point of showing any.
export const MAX_FACTS = 4;

// A synopsis is a legitimate mapped value and is three paragraphs long. It is
// cut here rather than by CSS so the DOM says what the row actually claims.
export const FACT_MAX_CHARS = 120;

// The one attribute in this list that fetches. D10 says the payload is data —
// it is rendered as text and never as markup — and an `<img src>` is the single
// place that stops being true, so the value has to earn it: https, or the
// inline image an uploaded file already produces. `http:` is refused with
// `javascript:` rather than separately; a mixed-content image is a broken image
// on every deployment this ships to.
const HTTPS_URL   = /^https:\/\/\S+$/i;
const INLINE_DATA = /^data:image\/[a-z0-9.+-]+;base64,/i;

export const isDisplayableImage = (value) => {
  if (typeof value !== 'string') return false;
  const src = value.trim();
  return HTTPS_URL.test(src) || INLINE_DATA.test(src);
};

/**
 * One value, as the one line of text a row can show for it.
 *
 * A list joins (a tag field arrives as one — `mapping.LIST_JOIN`'s separator is
 * `', '` and this matches it), an object does not: a geometry, or a nested
 * payload the binding maps deeper, has no reading as a fact and `[object
 * Object]` is worse than saying nothing. A boolean is skipped for a duller
 * reason — rendering one needs a word for true, and this module has no
 * translator by design.
 */
export const asText = (value) => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number') return String(value);
  if (Array.isArray(value)) {
    return value.map(asText).filter(Boolean).join(', ');
  }
  return '';
};

/** What the pick actually writes: present, and not filtered out by the host. */
const willFill = (value) => value !== null && value !== undefined && value !== '';

/**
 * `{ thumbnail, facts, fillCount }` for one candidate.
 *
 * `fieldMeta` is `[{name, label, field_type}]` — the form's own reading of its
 * fields, handed down by the host because only the host knows the *translated*
 * label and only the design knows the declared type. Absent, the row still
 * renders: the field's own name stands in as the label and nothing is a
 * picture. A renderer must tolerate what it is handed, which is `TagsField`'s
 * rule one module over.
 */
export const describeCandidate = (candidate, {
  fieldMeta = null, fillable = null, maxFacts = MAX_FACTS } = {}) => {
  const values = (candidate && candidate.values) || {};
  const meta = Array.isArray(fieldMeta) ? fieldMeta : [];
  const metaByName = new Map(meta.map((m) => [m.name, m]));
  const allowed = Array.isArray(fillable) ? new Set(fillable) : null;

  // The design's order where the host named one — the order the form itself
  // renders in, so the row reads the way the page below it does — then whatever
  // the binding mapped that the form does not show.
  const names = [
    ...meta.map((m) => m.name).filter((name) => name in values),
    ...Object.keys(values).filter((name) => !metaByName.has(name)),
  ];

  let thumbnail = null;
  for (const name of names) {
    if (metaByName.get(name)?.field_type !== 'image') continue;
    if (!isDisplayableImage(values[name])) continue;
    thumbnail = { field: name, src: asText(values[name]) };
    break;
  }

  const heading = asText(candidate && candidate.label).toLowerCase();
  const facts = [];
  for (const name of names) {
    if (facts.length >= maxFacts) break;
    // A second poster is not a fact, and the first one is already the picture.
    if (metaByName.get(name)?.field_type === 'image') continue;
    const text = asText(values[name]);
    if (!text) continue;
    // The label is the row's heading; printing it again buys nothing and costs
    // one of the four lines that distinguish this row from the next.
    if (text.toLowerCase() === heading) continue;
    facts.push({
      field: name,
      label: metaByName.get(name)?.label || name,
      text: text.length > FACT_MAX_CHARS ? `${text.slice(0, FACT_MAX_CHARS)}…` : text,
    });
  }

  const fillCount = names.filter(
    (name) => (!allowed || allowed.has(name)) && willFill(values[name])).length;

  return { thumbnail, facts, fillCount };
};
