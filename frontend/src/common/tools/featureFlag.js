import * as settings from '../../settings';

/**
 * Read a feature flag that may not be declared at all.
 *
 * `common/` is synced verbatim into the base template, where a feature module
 * — and therefore its flag — may simply not exist. Neither `import { GENERATOR }`
 * nor `settings.GENERATOR` survives that: webpack resolves both statically and
 * fails the build with "export 'GENERATOR' was not found", so the shared shell
 * could not mention a flag the deployment had never heard of.
 *
 * The lookup key is computed, which is the point — webpack cannot check it, and
 * an absent flag reads as what it honestly is: false unless the deployment says
 * otherwise.
 *
 *   {flag('GENERATOR') && <NavLink to="/licensing">…</NavLink>}
 */
export const flag = (name) => Boolean(settings[name]);

export default flag;
