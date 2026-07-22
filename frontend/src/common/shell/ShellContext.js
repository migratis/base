import { createContext, useContext } from 'react';

/**
 * ShellContext — the composition root injects the concrete auth primitives here
 * so shell components under `common/` (MenuLeft, Header, Layout, Home) never
 * import the `user` module directly. `App` (which owns the module wiring) fills
 * it via <ShellProvider value={{ useAuth, LoginComponent, userService }}>.
 *
 * Defaults are inert no-ops so a shell still renders (logged-out) if a provider
 * is missing — e.g. in isolated tests.
 */
const NOOP_USER_SERVICE = {
  logout: () => Promise.resolve({ detail: [{}] }),
  getProfile: () => Promise.resolve(null),
};

const ShellContext = createContext({
  // A hook the shell calls unconditionally: () => ({ user, setUser }).
  useAuth: () => ({ user: null, setUser: () => {} }),
  // The module's Login form component.
  LoginComponent: () => null,
  // The module's user service (logout / getProfile).
  userService: NOOP_USER_SERVICE,
});

export const ShellProvider = ShellContext.Provider;

export const useShell = () => useContext(ShellContext);

export default ShellContext;
