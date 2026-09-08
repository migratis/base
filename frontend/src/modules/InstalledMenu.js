import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  IoGridOutline as GridIcon,
  IoListOutline as ListIcon,
  IoPeopleOutline as PeopleIcon,
  IoCalendarOutline as CalendarIcon,
  IoMapOutline as MapIcon,
  IoCartOutline as CartIcon,
  IoDocumentTextOutline as DocumentIcon,
} from 'react-icons/io5';
import { moduleMenuItems, moduleRoles } from '../module_registry';
import { isMenuItemVisible } from '../common/tools/moduleRoles';

// The manifest names an icon; the shell decides what that looks like. An
// unknown name falls back rather than rendering an empty box — a menu entry
// with no icon is still a working menu entry.
const ICONS = {
  grid: GridIcon,
  list: ListIcon,
  people: PeopleIcon,
  calendar: CalendarIcon,
  map: MapIcon,
  cart: CartIcon,
  document: DocumentIcon,
};

/**
 * The installed applications' own navigation.
 *
 * `module_registry.js` is rebuilt by the installer and has always exported
 * `moduleMenuItems` (label, path, icon, module, min_list_role) alongside
 * `moduleRoles`; `common/tools/moduleRoles.js` has always exported
 * `isMenuItemVisible` to filter one against the other. Nothing imported
 * either, so an installed application appeared in the router and nowhere in
 * the sidebar — reachable only by typing its URL.
 *
 * This is the consumer. It lives outside `common/` on purpose: `common/` is
 * mirrored verbatim from the migratis repo, which has no installed modules and
 * no `module_registry.js` to read, so the shared shell cannot be the thing that
 * imports one.
 *
 * The label is the entity name the manifest carries. `t(label, label)` is the
 * generated list components' own idiom: translated when the app's namespace
 * seeds that key, the plain name when it does not — never a raw i18n slug.
 */
export const InstalledMenu = ({ onMobileClose }) => {
  const namespaces = [...new Set(moduleMenuItems.map((item) => item.module))];
  const { t } = useTranslation(namespaces.length ? namespaces : 'layout');

  const visible = moduleMenuItems.filter((item) => isMenuItemVisible(item, moduleRoles));
  if (!visible.length) return null;

  return (
    <>
      {visible.map((item) => {
        const Icon = ICONS[item.icon] || GridIcon;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
            onClick={onMobileClose}
          >
            <Icon />
            <span className="sidebar-label">
              {t(`${item.module}:${item.label}`, item.label)}
            </span>
          </NavLink>
        );
      })}
    </>
  );
};

export default InstalledMenu;
