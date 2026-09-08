import { InstalledMenu } from './InstalledMenu';
import { moduleMenuItems } from '../module_registry';

/**
 * The installed applications' contribution to the app shell, discovered by
 * common/shell/registry.js like any module's — so MenuLeft renders installed
 * apps without importing module_registry.js, which only this template has.
 *
 * `order: 10` puts them above the framework's own entries: the installed
 * application is what the user came for. A template with nothing installed
 * contributes nothing at all rather than an empty section.
 */
export const sidebar = [
  {
    id: 'installed-modules',
    order: 10,
    enabled: () => moduleMenuItems.length > 0,
    Component: InstalledMenu,
  },
];
