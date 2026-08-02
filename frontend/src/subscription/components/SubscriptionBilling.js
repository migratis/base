import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Subscription } from './Subscription';
import InvoiceList from '../../common/components/InvoiceList';
import { useShell } from '../../common/shell/ShellContext';

// The subscription module's column on Account → Billing: what a plan covers,
// subscribe / change / cancel, and the plan receipts only (credit purchases are
// listed by the credits column). Contributed through the shell registry's
// `billingSections` slot (see subscription/shell.js).
//
// The current plan lives on the user profile, which is read through
// ShellContext's injected `userService` rather than by importing the user
// module — a deployment without it falls back to the inert default and the
// block renders "no subscription" instead of crashing.
const SubscriptionBilling = () => {
  const { t } = useTranslation('subscription');
  const { userService } = useShell();
  const [subscription, setSubscription] = useState(null);

  useEffect(() => {
    userService.getProfile()
      .then((response) => { if (response && !response.detail) setSubscription(response.subscription); })
      .catch(() => {});
  }, [userService]);

  return (
    <section className="billing-column">
      <h5>{t('billing-subscription-title')}</h5>
      <p className="text-muted">{t('billing-subscription-description')}</p>
      <Subscription subscription={subscription} setSubscription={setSubscription} />
      {/* Plan invoices carry the plan's own label key, which lives in this
          module's namespace. */}
      <InvoiceList purpose="subscription" labelNs="subscription" />
    </section>
  );
};

export default SubscriptionBilling;
