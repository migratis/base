// Viewer-role resolution for installed modules — the framework-side mirror of
// each module's generated roles.py (and of the role logic the generated list
// components embed). The ladder per module comes from module_registry.js
// (moduleRoles), rebuilt by the installer from the module's manifest.
//
// Resolution, identical to the backend:
//   - no logged-in user            → the anonymous tier
//   - user.is_superuser            → the privileged (top) tier
//   - else highest ladder role among the user's auth groups,
//     defaulting to the lowest non-anonymous tier when none match.
//
// Auth Groups are namespaced "{module}:{role}" (installed apps are independent
// applications sharing only the login, so two apps that both define e.g. `admin`
// must not collapse onto one global Group). The viewer's groups therefore carry
// namespaced strings — resolution matches `${module}:${name}`, so the caller
// must pass the module the ladder belongs to.

const readUser = () => {
  try {
    const u = JSON.parse(localStorage.getItem('user') || 'null');
    return u && u.id ? u : null;
  } catch (e) {
    return null;
  }
};

export const resolveViewerRole = (ladder, module) => {
  if (!ladder || !ladder.ranks) return null;
  const user = readUser();
  if (!user) return ladder.anonymous;
  if (user.is_superuser) return ladder.privileged;
  const groups = new Set(user.groups || []);
  let best = ladder.default_auth;
  Object.entries(ladder.ranks).forEach(([name, rank]) => {
    if (groups.has(`${module}:${name}`) && rank > (ladder.ranks[best] ?? 0)) best = name;
  });
  return best;
};

// A menu entry is visible when the viewer's rank reaches the entry's
// min_list_role floor. Entries without a floor — or modules without a role
// ladder (legacy apps) — are always shown, never hidden on a guess.
export const isMenuItemVisible = (item, ladders) => {
  const floor = (item && item.min_list_role) || '';
  if (!floor) return true;
  const ladder = (ladders || {})[item.module];
  if (!ladder || !ladder.ranks) return true;
  const viewer = resolveViewerRole(ladder, item.module);
  const viewerRank = ladder.ranks[viewer];
  const floorRank = ladder.ranks[floor];
  if (viewerRank === undefined || floorRank === undefined) return true;
  return viewerRank >= floorRank;
};
