import { useEffect, useRef } from 'react';

import { hasStoredSession, sessionKnownAbsent, signalSessionExpired } from '../tools/session';

// A session ends on the server, in silence.
//
// Nothing reaches the browser when it does, so the tab left open over lunch
// goes on drawing the whole signed-in shell — the menu, the owner's name, every
// button their role allows — over a session that is gone. Until this hook, the
// only thing that ever noticed was a request the *user* made, which means the
// first sign of an expired session was an action of theirs failing: a save that
// did not save, or (through the AI transport) a paid refresh reported as "AI
// interpretation failed".
//
// So the shell asks. Not on a timer — a poll that fires every minute keeps a
// session alive on a backend whose expiry is idle-based, which is the one way
// to make this worse — but at the two moments that are worth a request:
//
//   * on mount, which is also how the copy is repaired when it went missing
//     while the session is alive (App 8's "I am connected and there is no Add
//     button"); and
//   * when the tab comes back to the foreground, which is both the moment the
//     answer stopped being current and the moment somebody is looking at it.
//
// Everything else is a guard against asking too often or asking at all:
// `"false"` is the server's own "there is no session" and is never asked again,
// a burst of focus/visibility events (they fire together on a tab switch) is
// one question, and once the wall is up the shell stops asking behind it.

// Far enough apart that alt-tabbing through a window does not make a request
// per pass, close enough that a session which died an hour ago is caught on the
// first look back at the tab.
export const SESSION_CHECK_MIN_INTERVAL_MS = 60 * 1000;

/**
 * Keep this browser's idea of who is logged in honest.
 *
 * @param {object}   options
 * @param {object}   options.userService  the shell's user service (getProfile).
 * @param {function} [options.onUser]     called with a freshly confirmed profile.
 * @param {boolean}  [options.enabled]    false stops the checks (the wall is up).
 */
export const useSessionWatch = ({ userService, onUser, enabled = true }) => {
  const lastCheck = useRef(0);
  const inFlight = useRef(false);
  // The callbacks are read through refs so that a parent re-rendering with a
  // new closure does not tear down and re-arm the listeners.
  const serviceRef = useRef(userService);
  const onUserRef = useRef(onUser);
  serviceRef.current = userService;
  onUserRef.current = onUser;

  useEffect(() => {
    if (!enabled) return undefined;

    let cancelled = false;

    const check = (force) => {
      // The one value that means "there is no session" rather than "we do not
      // know". Asking again would put a 401 in an anonymous visitor's console
      // on every page.
      if (sessionKnownAbsent()) return;
      if (inFlight.current) return;

      const now = Date.now();
      if (!force && now - lastCheck.current < SESSION_CHECK_MIN_INTERVAL_MS) return;
      lastCheck.current = now;
      inFlight.current = true;

      Promise.resolve()
        .then(() => serviceRef.current.getProfile())
        .then((fresh) => {
          if (cancelled) return;
          if (fresh && fresh.id) {
            // A live session. Refresh the copy while we are here: fields added
            // after login (the role groups, is_reviewer) arrive without a
            // re-login.
            try { localStorage.setItem('user', JSON.stringify(fresh)); } catch (e) { /* storage may be blocked */ }
            if (onUserRef.current) onUserRef.current(fresh);
            return;
          }
          // Anything else is a refusal body — the shared transport resolves
          // error responses, so a 401 arrives here as a `detail` and never as a
          // rejection. Storing that as an identity would make `user.id`
          // undefined and every later read a guess; signalling is what puts the
          // login modal up. On an anonymous visit this records "no session" and
          // announces nothing.
          signalSessionExpired('/user/getprofile');
        })
        .catch(() => {
          // A network blip is not an expired session, and claiming one would
          // wall a user whose wifi came back a second later. The next request
          // the page makes will settle it.
        })
        .finally(() => { inFlight.current = false; });
    };

    // The mount question is the one that repairs a missing copy, so it is not
    // subject to the throttle.
    check(true);

    const onVisible = () => {
      if (document.visibilityState === 'hidden') return;
      if (!hasStoredSession()) return;
      check(false);
    };

    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener('focus', onVisible);

    return () => {
      cancelled = true;
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener('focus', onVisible);
    };
  }, [enabled]);
};

export default useSessionWatch;
