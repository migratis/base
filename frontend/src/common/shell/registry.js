import { collect } from './collect';

/**
 * Shell contribution registry — the "find" half of the search/find/use
 * mechanism. At build time webpack's `require.context` scans every
 * `src/<module>/shell.js` and we collect whatever each one contributes, so the
 * shell (MenuLeft/Header/…) renders module snippets it never imported.
 *
 * A module opts in simply by dropping a `shell.js` that exports slot arrays:
 *
 *   // src/generator/shell.js
 *   import { LeftMenu } from './components/LeftMenu';
 *   import { GENERATOR } from '../settings';
 *   export const sidebar = [
 *     { id: 'generator', order: 20, enabled: () => GENERATOR, Component: LeftMenu },
 *   ];
 *
 * `require.context` is a webpack-only construct that does not exist under Jest,
 * so it is guarded — in the test environment `modules` stays empty (components
 * that read the registry simply render no slots, and tests that need slots mock
 * this module).
 */
let modules = [];

/* istanbul ignore next -- webpack-only discovery glue, exercised by the build */
try {
  // Static call so webpack can extract dependencies at build time. From
  // src/common/shell/ → src/ ; match one-level-deep <module>/shell.js only.
  const ctx = require.context('../../', true, /^\.\/[^/]+\/shell\.js$/);
  modules = ctx.keys().map((key) => ctx(key));
} catch (e) {
  // No require.context outside webpack (e.g. Jest) — components that read the
  // registry render no slots; tests that need slots mock this module.
}

export const sidebarSlots = collect(modules, 'sidebar');
export const headerWidgets = collect(modules, 'headerWidgets');
