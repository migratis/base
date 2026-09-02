import LookupControl from './components/LookupControl';
import { DATASOURCE } from '../settings';

/**
 * The datasource module's contribution to the app shell. Discovered
 * automatically by common/shell/registry.js.
 *
 * One slot only: the "fill this form from an external source" control a create
 * form renders above its fields. `common/` owns the form and must not import
 * this module, so the dependency runs the other way — which is also what makes
 * the module genuinely optional (SCOPE_external_data_sources.md@d2de531 §10
 * item 1). Nothing else in the frontend knows an external API exists.
 *
 * The `DATASOURCE` flag only says the module is installed; whether a button
 * appears is decided per entity by the declarations the application actually
 * carries, which is why an application with no source renders exactly today's
 * plain form.
 */
export const formLookups = [
  {
    id: 'datasource',
    order: 10,
    enabled: () => DATASOURCE,
    Control: LookupControl,
  },
];
