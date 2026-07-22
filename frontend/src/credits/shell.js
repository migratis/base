import CreditsIndicator from './components/CreditsIndicator';
import { CREDITS } from '../settings';

/**
 * Credits' contribution to the app shell. Discovered automatically by
 * common/shell/registry.js — the sidebar shows the compact balance widget,
 * the header shows the full one.
 */
const CompactIndicator = () => <CreditsIndicator compact />;
const HeaderIndicator = () => <CreditsIndicator />;

export const sidebar = [
  {
    id: 'credits',
    order: 10,
    enabled: () => CREDITS,
    Component: CompactIndicator,
  },
];

export const headerWidgets = [
  {
    id: 'credits',
    order: 10,
    enabled: () => CREDITS,
    Component: HeaderIndicator,
  },
];
