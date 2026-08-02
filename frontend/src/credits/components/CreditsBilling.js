import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { formatCredits } from '../../common/tools/formatCredits';
import { IoSparklesOutline as SparkleIcon, IoCartOutline as CartIcon } from 'react-icons/io5';
import StripeCheckoutModal from './StripeCheckoutModal';
import CreditsService from '../services/credits.service';
import InvoiceList from '../../common/components/InvoiceList';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';

// The credits module's column on Account → Billing: what credits are for, the
// current balance, a one-off Stripe Checkout to top it up, and the receipts for
// credit purchases only (the subscription column lists plan invoices).
// Contributed through the shell registry's `billingSections` slot (see
// credits/shell.js), so the user module renders it without importing — or even
// knowing about — this module.
const CreditsBilling = () => {
  const { t } = useTranslation('credits');
  const [usage, setUsage] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const loadUsage = useCallback(() => {
    CreditsService.getCredits()
      .then((data) => { if (data) setUsage(data); })
      .catch(() => {});
  }, []);

  useEffect(() => { loadUsage(); }, [loadUsage]);

  return (
    <section className="billing-column">
      <h5>{t('billing-credits-title')}</h5>
      <p className="text-muted">{t('billing-credits-description')}</p>
      {!usage && <LoaderIndicator />}
      {/* Credits are spent by everyone on human-lane AI; a subscription only
          covers the sandbox-approval charge, so there is no "unlimited"
          state — always show the balance + buy affordance (owner 2026-07-22). */}
      {usage &&
        <>
          <p><SparkleIcon />&nbsp;{t('billing-credits-balance', { credits: formatCredits(usage.credits) })}</p>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <CartIcon />&nbsp;{t('billing-buy-credits')}
          </button>
          <StripeCheckoutModal
            show={showModal}
            onHide={() => setShowModal(false)}
            onSuccess={() => { setShowModal(false); loadUsage(); }}
            currentUsage={usage}
          />
        </>
      }
      {/* Credit purchases are invoiced under the shared `billing` namespace
          (`credits-purchase`), not this module's own. */}
      <InvoiceList purpose="credits" labelNs="billing" />
    </section>
  );
};

export default CreditsBilling;
