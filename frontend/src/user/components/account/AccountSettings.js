import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';
import Profile from '../Profile';
import Preferences from './Preferences';
import ApiAccess from './ApiAccess';
import Billing from './Billing';
import { PageShell, PagePanel } from '../../../common/components/PageShell';
import { enabledSlots } from '../../../common/shell/collect';
import { billingSections } from '../../../common/shell/registry';

// Consolidated Account settings hub (/account). Folds the previously scattered
// per-account surfaces into one tabbed page (SCOPE_account_settings §3):
//   - Profile     → the existing Profile component (identity, password, delete,
//                   subscription) relocated rather than duplicated.
//   - Preferences → persisted interface language.
//   - API access  → Personal Access Token management (the agent-lane credential,
//                   the genuinely new capability this scope adds).
//   - Billing     → whatever monetization blocks the deployed modules contribute
//                   (credits, plans). The tab exists only when at least one is
//                   enabled, so this page never names a module it does not own.
// Security (2FA UI) / Danger-zone polish are deferred per §5.
const AccountSettings = () => {
  const { t } = useTranslation('account');
  const [ searchParams, setSearchParams ] = useSearchParams();
  const active = searchParams.get('tab') || 'profile';
  const hasBilling = enabledSlots(billingSections).length > 0;

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
        <Tab eventKey="api" title={t('api-access')}>
          <PagePanel><ApiAccess /></PagePanel>
        </Tab>
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
