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

/**
 * The slots a host should actually render, in `order`. A descriptor without an
 * `enabled` predicate is always on (feature flags are optional).
 *
 * @param {object[]} slots  collected slot descriptors
 * @returns {object[]} the enabled subset, order preserved
 */
export function enabledSlots(slots) {
  return (slots || []).filter((slot) => !slot.enabled || slot.enabled());
}

/**
 * Winner-takes-all resolution for slots that carry a *value* rather than a
 * component — e.g. where to land after login, or which page documents the
 * agent-lane token. The lowest-`order` enabled contributor wins; `undefined`
 * when no module contributes, so the host can fall back to its own default.
 *
 * @param {object[]} slots  collected slot descriptors
 * @returns {object|undefined} the winning descriptor
 */
export function firstEnabled(slots) {
  return enabledSlots(slots)[0];
}
