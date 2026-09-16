// SCOPE_composed_pages.md §13 — a per-app page-block component, in its envelope.
//
// **The props contract is closed, and this file is where it is closed.** App 2's
// components read `entityConfig.embedded_children` — a key of the *authoring
// spec* that is `undefined` at runtime — and two of three crashed on first
// render. A page block receives exactly:
//
//   {records, aggregate, pageContext, blockConfig, t, viewAs, onSelectRecord}
//
// and nothing else, because nothing else is spread here. `static_lint` refuses
// a component that reaches past it; this is what makes that refusal true rather
// than merely stated.
//
// The compiled component arrives as a prop. Compiling needs `new Function` and
// the four injected names, which live with the display compiler — a file that
// sits at a different path in each tree (`generator/…/display/` here,
// `common/components/display/` in base). So the HOST compiles and this renders,
// which is the `routeSnappers` shell-registry rule: `common/` never imports a
// feature module, and the two hosts differ in exactly one thing.

const CustomBlock = ({
  Component, records, aggregate, pageContext, blockConfig, t, viewAs,
  onSelectRecord,
}) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);

  if (!Component) {
    // Named, registered, refused by the lint, or simply not authored yet — the
    // block says so rather than showing a blank rectangle, which is the one
    // thing a composed page must never do.
    return (
      <p className="page-block-unavailable">
        {tval('page-block-component-missing',
          'This block’s component is not available.')}
      </p>
    );
  }

  return (
    <Component
      records={Array.isArray(records) ? records : []}
      aggregate={aggregate === undefined ? null : aggregate}
      pageContext={pageContext || {}}
      blockConfig={blockConfig || {}}
      t={t}
      viewAs={viewAs}
      onSelectRecord={onSelectRecord}
    />
  );
};

export default CustomBlock;
