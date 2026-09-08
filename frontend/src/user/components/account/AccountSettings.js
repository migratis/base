import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';
import Profile from '../Profile';
import Preferences from './Preferences';
import ApiAccess from './ApiAccess';
import Billing from './Billing';
import UserService from '../../services/user.service';
import { PageShell, PagePanel } from '../../../common/components/PageShell';
import { enabledSlots } from '../../../common/shell/collect';
import { billingSections } from '../../../common/shell/registry';

// Consolidated My Account hub (/account). Folds the previously scattered
// per-account surfaces into one tabbed page (SCOPE_account_settings §3):
//   - Profile     → the existing Profile component (identity, password, delete,
//                   subscription) relocated rather than duplicated.
//   - Preferences → persisted interface language.
//   - API access  → Personal Access Token management (the agent-lane credential,
//                   the genuinely new capability this scope adds). Present only
//                   when the user service manages tokens at all.
//   - Billing     → whatever monetization blocks the deployed modules contribute
//                   (credits, plans). The tab exists only when at least one is
//                   enabled, so this page never names a module it does not own.
// Security (2FA UI) / Danger-zone polish are deferred per §5.
const AccountSettings = () => {
  const { t } = useTranslation('account');
  const [ searchParams, setSearchParams ] = useSearchParams();
  const hasBilling = enabledSlots(billingSections).length > 0;
  // Same rule as Billing, one capability over: this page never names a surface
  // the deployment does not have. Personal access tokens are the agent-lane
  // credential and they live in the user SERVICE — the base template ships a
  // user module deliberately built without them (no PAT model, no endpoints,
  // no service methods), and the tab rendered anyway, so ApiAccess called
  // UserService.listTokens on mount and took the whole hub down with
  // "listTokens is not a function". Asking the service is the honest question:
  // there is no module to key a flag on, because tokens are part of `user`.
  const hasTokens = typeof UserService.listTokens === 'function';
  // A `?tab=` link outlives the tab it points at — a bookmarked `?tab=billing`
  // survives a deployment switching its monetization modules off. Fall back to
  // the first tab rather than selecting a key no `<Tab>` claims, which leaves
  // the pane blank.
  const available = [
    'profile',
    'preferences',
    ...(hasTokens ? ['api'] : []),
    ...(hasBilling ? ['billing'] : []),
  ];
  const requested = searchParams.get('tab');
  const active = available.includes(requested) ? requested : 'profile';

  const selectTab = (key) => {
    setSearchParams({ tab: key });
  };

  return (
    /* The tab strip is navigation and belongs above the surface; each pane
       gets its own panel so switching tabs swaps the content of one card
       rather than redrawing the page. */
    <PageShell title={t('account-settings')} panel={false}>
      <Tabs activeKey={active} onSelect={selectTab}>
        <Tab eventKey="profile" title={t('profile')}>
          <PagePanel><Profile /></PagePanel>
        </Tab>
        <Tab eventKey="preferences" title={t('preferences')}>
          <PagePanel><Preferences /></PagePanel>
        </Tab>
        {hasTokens &&
          <Tab eventKey="api" title={t('api-access')}>
            <PagePanel><ApiAccess /></PagePanel>
          </Tab>
        }
        {hasBilling &&
          <Tab eventKey="billing" title={t('billing')}>
            <PagePanel><Billing /></PagePanel>
          </Tab>
        }
      </Tabs>
    </PageShell>
  );
};

export default AccountSettings;
