// SCOPE_composed_pages.md §3 — fixed prose on a page. The one block kind with
// no subject at all.
//
// The text is `blockConfig.body`, and in a generated application it arrives as
// an i18n key that `_build_seed_translations` seeded as an identity row — the
// single-language rule for generated apps. In the sandbox it arrives as the
// prose the owner typed. Both are strings, and `t` resolves the first and
// passes the second through, so this component never learns which host it is in.

const LEVELS = { 1: 'h2', 2: 'h3', 3: 'h4', 4: 'h5' };

const TextBlock = ({ blockConfig = {}, t }) => {
  const body = blockConfig.body || '';
  if (!body) return null;
  const text = t ? t(body, body) : body;
  const Heading = LEVELS[blockConfig.heading_level];

  // Deliberately NOT HTML. `sanitizeHtml` is in the custom-component compile
  // scope for authors who need markup; a built-in block rendering owner-typed
  // prose as HTML would put an injection point on every page for the sake of
  // a bold word.
  return Heading
    ? <Heading className="page-block-text">{text}</Heading>
    : <p className="page-block-text">{text}</p>;
};

export default TextBlock;
