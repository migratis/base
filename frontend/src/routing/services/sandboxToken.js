/**
 * The sandbox token this page is a preview of, read from the address bar.
 *
 * `POST /routing/snap` on migratis stands in front of an external, metered
 * routing quota, so it asks for a token of a sandbox we published
 * (SCOPE_routing_sandbox_external.md@c170e1a §6). That is a far tighter gate than
 * throttling alone and it costs anonymous visitors nothing — the token is the
 * value already in the link they were given.
 *
 * Read from the URL rather than threaded through props for two reasons. The map
 * field lives in `common/`, which must never learn that a road graph or a
 * sandbox token exists; and a token passed by hand is a token a future caller
 * forgets, at which point every snap 403s and the line quietly goes straight.
 *
 * Both sandbox routes match: `/sandbox/:token` and
 * `/sandbox/:token/simulate/:stepId`. Anywhere else there is no token, the
 * header is omitted, and the backend answers `routing-snap-forbidden` — which
 * the editor already degrades on by keeping the traced line and badging it.
 *
 * In a generated application there is no sandbox and therefore never a token,
 * so this always returns '' and the header never appears. That is correct
 * there: an installed app's `/routing/snap` stays open, because its
 * anonymous-role case is real and the engine it calls is its owner's own. The
 * divergence between the two deployments is a *setting*
 * (`ROUTING_SNAP_AUTHORIZER`), never a fork of this file.
 */
const SANDBOX_PATH = /^\/sandbox\/([^/?#]+)/;

export const SANDBOX_TOKEN_HEADER = 'X-Sandbox-Token';

export function sandboxToken(pathname) {
  const path =
    typeof pathname === 'string'
      ? pathname
      : (typeof window !== 'undefined' && window.location && window.location.pathname) || '';
  const match = SANDBOX_PATH.exec(path);
  return match ? decodeURIComponent(match[1]) : '';
}

/** `{ headers: { … } }` to spread into a request, or `{}` when there is no token. */
export function sandboxAuthConfig(pathname) {
  const token = sandboxToken(pathname);
  return token ? { headers: { [SANDBOX_TOKEN_HEADER]: token } } : {};
}
