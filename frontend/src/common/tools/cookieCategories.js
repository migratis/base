/**
 * common/tools/cookieCategories.js
 * --------------------------------
 * The four purposes a deployment may store something for, and which of them
 * the visitor has to be asked about first.
 *
 * ePrivacy Article 5(3) exempts storage that is strictly necessary to provide
 * the service the visitor explicitly asked for — the session that keeps them
 * signed in, the token that protects a form, the language they picked, the
 * record of this very choice. Everything else needs consent *before* it is
 * stored, and must stay refusable afterwards (GDPR Article 7(3)).
 *
 * `NECESSARY` is therefore not a category the visitor can switch off, and no
 * other category may ever be treated as one. The values match
 * `migratis.cookie.models.Cookie`'s own: the published inventory is the single
 * declaration of what this deployment stores, and these are the labels it is
 * read through.
 */

export const NECESSARY = 'necessary';
export const PREFERENCES = 'preferences';
export const STATISTICS = 'statistics';
export const MARKETING = 'marketing';

// Reading order: what cannot be refused first, then in increasing order of
// intrusiveness. Alphabetical would open the list on 'marketing'.
export const CATEGORY_ORDER = [NECESSARY, PREFERENCES, STATISTICS, MARKETING];

// The exemption, in one place. A category is refusable unless it is in here.
export const EXEMPT_CATEGORIES = [NECESSARY];

export const requiresConsent = (category) =>
  !EXEMPT_CATEGORIES.includes(category);

/** The refusable categories this file knows of, in reading order. */
export const consentRequiringCategories = () =>
  CATEGORY_ORDER.filter(requiresConsent);

/**
 * Whether this published inventory entry may be stored without being asked.
 *
 * The backend answers this itself (`Cookie.requires_consent`, derived from the
 * same category), and where it has, its answer wins. The two tables have to
 * agree and **neither container can read the other's tree** — the backend
 * decides what is published, the browser decides what is gated — so wherever
 * an inventory exists it is the one authority, and `requiresConsent` above is
 * left to do only the job that cannot wait for it: answering synchronously,
 * before any fetch, where the conservative reading is already the safe one.
 */
export const entryRequiresConsent = (entry) => (
  typeof entry?.requires_consent === 'boolean'
    ? entry.requires_consent
    : requiresConsent(entry?.category)
);

/**
 * The refusable categories this inventory actually contains, in reading order.
 *
 * Empty means there is nothing to ask about, which is what turns the notice
 * into a statement and hides the switches on /cookies.
 */
export const refusableCategories = (entries) => {
  const present = new Set(
    (entries || []).filter(entryRequiresConsent).map((item) => item.category)
  );
  const known = CATEGORY_ORDER.filter((category) => present.has(category));
  // A category the backend calls refusable and this file has never heard of is
  // still refusable; it goes last rather than being dropped.
  const extra = [...present].filter((c) => !CATEGORY_ORDER.includes(c)).sort();
  return [...known, ...extra];
};

/**
 * Sort an inventory into `{ category: entries }`, keeping the reading order
 * and dropping categories this deployment stores nothing for — an empty
 * "Marketing" heading on a site that serves no advertising reads as a
 * disclosure that something is being withheld.
 */
export const groupByCategory = (entries) => {
  const groups = [];
  CATEGORY_ORDER.forEach((category) => {
    const members = (entries || []).filter((item) => item.category === category);
    if (members.length) groups.push({ category, entries: members });
  });
  // A category the backend knows about and this file does not: published
  // rather than silently dropped, because the one thing a storage disclosure
  // may not do is leave something out.
  const known = new Set(CATEGORY_ORDER);
  const unknown = [...new Set(
    (entries || []).map((item) => item.category).filter((c) => !known.has(c))
  )].sort();
  unknown.forEach((category) => groups.push({
    category,
    entries: (entries || []).filter((item) => item.category === category),
  }));
  return groups;
};
