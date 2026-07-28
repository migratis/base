import SubscriptionBilling from './components/SubscriptionBilling';
import { SUBSCRIPTION } from '../settings';

/**
 * Subscription's contribution to the app shell. Discovered automatically by
 * common/shell/registry.js — Account → Billing renders the plan management
 * block without the user module importing this module or testing its flag.
 */
export const billingSections = [
  {
    id: 'subscription',
    order: 20,
    enabled: () => SUBSCRIPTION,
    Component: SubscriptionBilling,
  },
];
