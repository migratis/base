/**
 * common/tools/cookieConsent.js
 * -----------------------------
 * The visitor's recorded choice about storage on their device, and the one
 * place that reads or writes it.
 *
 * Four rules the previous banner broke, each of which is a legal requirement
 * rather than a preference:
 *
 * 1. **Silence is not consent.** The old banner said "by continuing to visit
 *    this site you agree" and recorded an accept the moment anything was
 *    clicked. Continued browsing has never been consent (CJEU *Planet49*,
 *    C-673/17; EDPB Guidelines 05/2020 §86), so a visitor who has chosen
 *    nothing is recorded as having chosen nothing, and `hasConsent` answers
 *    `false` for every refusable category until they do.
 *
 * 2. **Refusing has to do something.** `setConsent` clears the storage of
 *    every category it was not given, from the published inventory, so a
 *    refusal removes what a previous acceptance left behind instead of only
 *    changing a flag.
 *
 * 3. **Withdrawal is as easy as giving** (GDPR Article 7(3)): the same
 *    function records both, and the /cookies page calls it.
 *
 * 4. **A choice is made about a known list.** `VERSION` is stored with the
 *    choice, so adding a category to the inventory re-asks rather than
 *    inheriting a permission for something that did not exist when it was
 *    given.
 *
 * The record itself is exempt storage — it exists only to stop us asking
 * again, which is the service the visitor asked for by answering.
 */

import Cookies from 'js-cookie';

import {
  NECESSARY, entryRequiresConsent, requiresConsent,
} from './cookieCategories';

/** The cookie holding the choice. Declared in the published inventory. */
export const CONSENT_COOKIE = 'mg_consent';

/**
 * Bumping this re-asks everyone.
 *
 * Version 1 is deliberately a fresh start rather than a reading of `spcc1`,
 * the cookie the old banner set. `spcc1` recorded an acceptance obtained by
 * telling the visitor that carrying on browsing was agreement — so it is not
 * a record of a choice, and treating it as one would mean the visitor never
 * sees the corrected notice. `forgetRetiredRecords` deletes it instead: we no
 * longer set it, and storage we no longer set has no business staying on
 * somebody's device or in our inventory.
 */
export const VERSION = 1;

// CNIL/CNPD guidance: ask again after six months rather than keeping a choice
// indefinitely.
const RETENTION_DAYS = 180;

const RETIRED_COOKIES = ['spcc1'];

const CHANGE_EVENT = 'migratis:consent-change';

const cookieAttributes = () => ({
  expires: RETENTION_DAYS,
  path: '/',
  sameSite: 'strict',
  // The record is read by this script, so it cannot be HttpOnly; `secure`
  // follows the page so a local http dev server still works.
  secure: typeof window !== 'undefined' && window.location.protocol === 'https:',
});

/**
 * The stored choice, or `null` when the visitor has not answered.
 *
 * Returns `null` for a record written against another `VERSION` too: a
 * permission given for a list of categories is not a permission for a
 * different list.
 */
export const getConsent = () => {
  let raw;
  try {
    raw = Cookies.get(CONSENT_COOKIE);
  } catch (e) {
    // A browser with storage blocked altogether: nothing was stored, so
    // nothing was consented to.
    return null;
  }
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || parsed.v !== VERSION || !Array.isArray(parsed.c)) return null;
    return { categories: parsed.c, decidedAt: parsed.t || null };
  } catch (e) {
    return null;
  }
};

/** Whether the visitor has answered at all. */
export const hasDecided = () => getConsent() !== null;

/**
 * Whether this category may be stored right now.
 *
 * Synchronous and safe to call before the inventory has loaded, which is what
 * makes it usable as the gate in front of a script: an exempt category is
 * always allowed, and a refusable one is allowed only by an explicit record.
 */
export const hasConsent = (category) => {
  if (!requiresConsent(category)) return true;
  const consent = getConsent();
  return !!consent && consent.categories.includes(category);
};

/**
 * Record a choice.
 *
 * `categories` is what the visitor allowed; `NECESSARY` is added whether or
 * not it was passed, because it was never theirs to refuse and a record that
 * omits it would read as a refusal of the session they are using.
 * `inventory` is the published list, used to clear what was refused.
 */
export const setConsent = (categories, inventory) => {
  const allowed = [NECESSARY, ...(categories || []).filter(requiresConsent)];
  const unique = [...new Set(allowed)];
  try {
    Cookies.set(
      CONSENT_COOKIE,
      JSON.stringify({ v: VERSION, c: unique, t: new Date().toISOString() }),
      cookieAttributes(),
    );
  } catch (e) {
    // Storage blocked. Nothing is recorded, so nothing is treated as allowed
    // — the notice will ask again, which is the honest outcome.
  }
  clearRefused(unique, inventory);
  announce();
  return unique;
};

/**
 * Forget the record, so the notice asks again.
 *
 * The /cookies page offers this: a visitor who may give a choice has to be
 * able to take it back, and taking it back means the refusable storage goes
 * with it.
 */
export const clearConsent = (inventory) => {
  try {
    Cookies.remove(CONSENT_COOKIE, { path: '/' });
  } catch (e) { /* storage blocked */ }
  clearRefused([NECESSARY], inventory);
  announce();
};

/**
 * Delete the cookies and keys of every refusable category the visitor did not
 * allow.
 *
 * Driven by the published inventory rather than a second list kept here: the
 * disclosure and the deletion then cannot disagree about what exists, and an
 * entry nobody declared is an entry nobody can be shown either.
 */
export const clearRefused = (allowed, inventory) => {
  const permitted = new Set(allowed || []);
  (inventory || []).forEach((entry) => {
    // The published `requires_consent` decides, not this file's own table:
    // deleting is the consequential half, and the two must not be able to
    // disagree about whether an entry was ever the visitor's to refuse.
    if (!entryRequiresConsent(entry)) return;
    if (permitted.has(entry.category)) return;
    forget(entry);
  });
};

/** Remove the storage this inventory entry describes. */
const forget = (entry) => {
  try {
    if (entry.storage === 'local_storage') {
      window.localStorage.removeItem(entry.name);
    } else if (entry.storage === 'session_storage') {
      window.sessionStorage.removeItem(entry.name);
    } else {
      Cookies.remove(entry.name, { path: '/' });
      // A third party may have scoped it to the registrable domain rather
      // than to this host, in which case the path-only removal is a no-op.
      const host = window.location.hostname;
      const parts = host.split('.');
      if (parts.length > 2) {
        Cookies.remove(entry.name, { path: '/', domain: `.${parts.slice(-2).join('.')}` });
      }
      Cookies.remove(entry.name, { path: '/', domain: host });
    }
  } catch (e) {
    // A blocked or absent storage area is already in the state we want.
  }
};

/**
 * Delete storage this deployment used to set and no longer does.
 *
 * Called once on mount. Leaving `spcc1` behind would mean a cookie on the
 * visitor's device that appears in no disclosure, which is the same defect as
 * an undeclared cookie we do set.
 */
export const forgetRetiredRecords = () => {
  RETIRED_COOKIES.forEach((name) => {
    try {
      Cookies.remove(name, { path: '/' });
    } catch (e) { /* storage blocked */ }
  });
};

const announce = () => {
  try {
    window.dispatchEvent(new Event(CHANGE_EVENT));
  } catch (e) { /* no window, e.g. a non-DOM test environment */ }
};

/** Subscribe to choices made anywhere in the app. Returns the unsubscribe. */
export const onConsentChange = (handler) => {
  window.addEventListener(CHANGE_EVENT, handler);
  return () => window.removeEventListener(CHANGE_EVENT, handler);
};
