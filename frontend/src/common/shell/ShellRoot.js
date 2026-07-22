import { ShellProvider } from './ShellContext';
import { shellProviders, authService } from './registry';

/**
 * ShellRoot wraps the app at the very root. It mounts every context provider
 * that modules contributed (via `providers` in their shell.js) and injects the
 * discovered auth service into ShellContext.
 *
 * Because auth is discovered rather than imported, a deployment WITHOUT the
 * user module simply contributes no provider and no auth service — the shell
 * then uses ShellContext's inert defaults and renders logged-out. Nothing in
 * common/ or the composition root imports the user module directly.
 */
export const ShellRoot = ({ children }) => {
  // Nest discovered providers outermost-first (earliest `order` = outermost).
  const withProviders = shellProviders.reduceRight(
    (acc, { Provider }) => <Provider>{acc}</Provider>,
    children
  );

  // `value={undefined}` makes React fall back to the ShellContext default.
  return <ShellProvider value={authService}>{withProviders}</ShellProvider>;
};

export default ShellRoot;
