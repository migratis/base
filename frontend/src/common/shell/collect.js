/**
 * Pure collector for shell contributions.
 *
 * Each feature module may expose a `src/<module>/shell.js` that exports named
 * arrays of *slot descriptors* (e.g. `sidebar`, `headerWidgets`). This helper
 * flattens the descriptors found across all discovered modules for a given key
 * and returns them ordered by their optional `order` field (default 0).
 *
 * Kept free of any webpack (`require.context`) magic so it is unit-testable in
 * plain Jest — the discovery glue lives in `registry.js`.
 *
 * @param {object[]} modules  imported module namespaces (may contain nulls)
 * @param {string}   key      contribution key to collect (e.g. 'sidebar')
 * @returns {object[]} ordered slot descriptors
 */
export function collect(modules, key) {
  return (modules || [])
    .filter(Boolean)
    .flatMap((mod) => (Array.isArray(mod[key]) ? mod[key] : []))
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
}
