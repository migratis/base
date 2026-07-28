import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Subscription } from './Subscription';
import { useShell } from '../../common/shell/ShellContext';

// The subscription module's block on Account → Billing: subscribe to, change,
// or cancel a recurring plan. Contributed through the shell registry's
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
    <section>
      <h5>{t('billing-subscription-title')}</h5>
      <Subscription subscription={subscription} setSubscription={setSubscription} />
    </section>
  );
};

export default SubscriptionBilling;
