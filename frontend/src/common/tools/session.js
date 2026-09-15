// What a 401 means, in one place.
//
// Who is logged in lives in an HttpOnly session cookie the page cannot read;
// `localStorage.user` is only this browser's copy of it. When the session ends
// — an expiry, a server restart, a logout in another tab — the copy is what is
// left, and every role gate, every menu entry and the whole signed-in shell go
// on being drawn over a session that is gone.
//
// This rule used to be written out twice, once per transport, and the second
// copy had drifted: `generator.axios` raised the flag and left `user` standing,
// while the Layout's listener returns early exactly while a copy is standing.
// So an expired session discovered by a paid AI call produced no login modal at
// all — just "AI interpretation failed" — and left a `session_expired` flag
// behind to wall whichever private page was opened next.
//
// The order matters and is the reason this is a function rather than two lines:
// the copy is cleared BEFORE the event is dispatched, because the listener
// reads the copy to decide whether the signal is real.

export const SESSION_EXPIRED_EVENT = 'session-expired';

/**
 * Record that the API answered 401, and say so if a session actually ended.
 *
 * Only a session that existed can expire. A 401 on an anonymous visit means
 * "not logged in", which is a perfectly legal state on a public page — raising
 * the flag there left it in localStorage and prompted for a login on the next
 * page, whichever page that was. The "no session" answer is still stored, since
 * `"false"` is what stops the shell asking the server again on every page.
 *
 * @param {string} [url] the request that was refused, carried for the listener.
 * @returns {boolean} whether a live session was the thing that ended.
 */
export const signalSessionExpired = (url) => {
  let hadSession = false;
  try {
    const stored = localStorage.getItem('user');
    hadSession = !!stored && stored !== 'false';
    localStorage.setItem('user', false);
    if (hadSession) localStorage.setItem('session_expired', 'true');
  } catch (e) {
    // Storage can be unavailable (private mode, blocked cookies). The signal is
    // still worth dispatching for a shell that is currently mounted.
  }

  if (!hadSession) return false;

  window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT, { detail: { url } }));
  return true;
};

/** Does this browser believe it is signed in? */
export const hasStoredSession = () => {
  try {
    const stored = localStorage.getItem('user');
    return !!stored && stored !== 'false';
  } catch (e) {
    return false;
  }
};

/** Has the server already answered "there is no session"? */
export const sessionKnownAbsent = () => {
  try {
    return localStorage.getItem('user') === 'false';
  } catch (e) {
    return false;
  }
};
