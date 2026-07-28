import { useTranslation } from 'react-i18next';
import { enabledSlots } from '../../../common/shell/collect';
import { billingSections } from '../../../common/shell/registry';

// Consolidated Billing surface (Account Settings › Billing). The user module
// owns the *place*, not the monetization surfaces: each module contributes its
// own block through the shell registry's `billingSections` slot — credits
// (credits/shell.js) and plans (subscription/shell.js) today. That keeps this
// page free of imports and feature flags belonging to modules it does not own,
// and a deployment shipping neither simply never reaches here (AccountSettings
// hides the tab).
const Billing = () => {
  const { t } = useTranslation('account');

  return (
    <div className="billing">
      <p className="text-muted">{t('billing-intro')}</p>
      { enabledSlots(billingSections).map(({ id, Component }) => <Component key={id} />) }
    </div>
  );
};

export default Billing;
