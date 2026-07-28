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

// Extra blocks a module adds to Account → Preferences (e.g. the generator's
// default-LLM picker). Keeps the user module from importing feature modules to
// render settings that are not its own.
export const accountSections = collect(modules, 'accountSections');

// Blocks a module adds to Account → Billing (credits, subscription, …). The
// tab itself only exists when at least one module contributes an enabled
// section, so a deployment that monetizes nothing simply never shows it.
export const billingSections = collect(modules, 'billingSections');

// Where an authenticated session should land ({ path }). Winner-takes-all via
// `firstEnabled` — the lowest-`order` enabled contributor wins and the user
// module falls back to /home when no feature module claims a landing page.
export const landingRoutes = collect(modules, 'landingRoutes');

// The in-app page documenting the token-authenticated API ({ path }), published
// by whichever module exposes it. Winner-takes-all; Account → API access hides
// the "read the docs" hint entirely when nothing is contributed.
export const tokenDocs = collect(modules, 'tokenDocs');

// Context providers a module needs mounted at the app root (e.g. the user
// module's AuthProvider). Rendered by ShellRoot, outermost-first by `order`.
export const shellProviders = collect(modules, 'providers');

// The auth service a module injects into ShellContext ({ useAuth,
// LoginComponent, userService }). Optional: a deployment without the user
// module contributes none, and the shell falls back to ShellContext's no-op
// defaults (renders logged-out). First contributor wins.
const authModule = modules.filter(Boolean).find((mod) => mod.auth);
export const authService = authModule ? authModule.auth : undefined;
