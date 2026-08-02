import { useTranslation } from 'react-i18next';
import { enabledSlots } from '../../../common/shell/collect';
import { billingSections } from '../../../common/shell/registry';

// Consolidated Billing surface (My Account › Billing). The user module
// owns the *place*, not the monetization surfaces: each module contributes its
// own block through the shell registry's `billingSections` slot — credits
// (credits/shell.js) and plans (subscription/shell.js) today. That keeps this
// page free of imports and feature flags belonging to modules it does not own,
// and a deployment shipping neither simply never reaches here (AccountSettings
// hides the tab).
//
// Layout: the sections sit side by side in a grid row, in slot order — credits
// first, subscription second. The page owns the columns, not the sections, so
// it is the page that has to make sense whichever modules a deployment
// activated: two enabled sections split the row in half, a lone one takes the
// full width rather than leaving dead space beside it, and none at all is a
// case AccountSettings resolves by hiding the tab entirely.
const Billing = () => {
  const { t } = useTranslation('account');
  const sections = enabledSlots(billingSections);
  const columnClass = sections.length > 1 ? 'col-12 col-md-6' : 'col-12';

  return (
    <div className="billing">
      <p className="text-muted">{t('billing-intro')}</p>
      <div className="row">
        { sections.map(({ id, Component }) =>
          <div className={columnClass} key={id}>
            <Component />
          </div>
        )}
      </div>
    </div>
  );
};

export default Billing;
