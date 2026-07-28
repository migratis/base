import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';
import Profile from '../Profile';
import Preferences from './Preferences';
import ApiAccess from './ApiAccess';
import Billing from './Billing';
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
    <>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>{t('account-settings')}</h2>
          </div>
        </div>
      </header>
      <Tabs activeKey={active} onSelect={selectTab} className="mb-3">
        <Tab eventKey="profile" title={t('profile')}>
          <Profile />
        </Tab>
        <Tab eventKey="preferences" title={t('preferences')}>
          <Preferences />
        </Tab>
        <Tab eventKey="api" title={t('api-access')}>
          <ApiAccess />
        </Tab>
        {hasBilling &&
          <Tab eventKey="billing" title={t('billing')}>
            <Billing />
          </Tab>
        }
      </Tabs>
    </>
  );
};

export default AccountSettings;
