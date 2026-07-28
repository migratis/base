import CreditsIndicator from './components/CreditsIndicator';
import CreditsBilling from './components/CreditsBilling';
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

/**
 * Account → Billing: balance + top-up. Buying credits is a credits concern, so
 * the account page renders it through the slot instead of importing this module
 * behind another module's feature flag.
 */
export const billingSections = [
  {
    id: 'credits',
    order: 10,
    enabled: () => CREDITS,
    Component: CreditsBilling,
  },
];
