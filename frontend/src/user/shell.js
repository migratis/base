import { useAuth, AuthProvider } from './hooks/useAuth';
import Login from './components/Login';
import UserService from './services/user.service';

/**
 * The user module's contribution to the app shell. Discovered automatically by
 * common/shell/registry.js, so neither common/ nor the composition root imports
 * the user module directly — a generated app that omits the user feature simply
 * ships no user/shell.js and the shell degrades to logged-out defaults.
 */
export const providers = [
  { id: 'auth', order: 0, Provider: AuthProvider },
];

export const auth = {
  useAuth,
  LoginComponent: Login,
  userService: UserService,
};
