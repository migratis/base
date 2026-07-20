import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import SubscriptionService from '../services/subscription.service';
import Table from 'react-bootstrap/Table';
import { IoCardOutline as CardOutline } from 'react-icons/io5';
import { toast } from 'react-toastify';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';
import DOMPurify from 'dompurify';
import UserService from "../../user/services/user.service";
import { useOutletContext, useNavigate, useSearchParams } from "react-router-dom";
import { TRIAL } from "../../settings";

const Subscribe = () => {
  const { t } = useTranslation(['subscription', 'billing']);
  // eslint-disable-next-line
  const { user, setUser } = useOutletContext();
  const [ plans, setPlans ] = useState([]);
  const [ processing, setProcessing ] = useState(false);
  const navigate = useNavigate();
  const [ searchParams, setSearchParams ] = useSearchParams();
  // Trial is offered only when the frontend TRIAL flag is on AND the backend
  // marks the user trial-eligible (user.trial, gated by SUBSCRIPTION_TRIAL).
  const showTrial = TRIAL && !!(user && user.trial);

  // After returning from Checkout, poll the profile until the webhook has
  // activated access, then land the user on their account.
  const refreshUser = (attempt) => {
    if (attempt > 5) {
      toast.error(t('subscription-error'));
      setProcessing(false);
      return;
    }
    UserService.refreshUser().then((response) => {
      if (response.user && response.user.subscription && response.user.subscription.access) {
        const storedUser = {
          id: response.user.id,
          trial: response.user.trial,
          subscription: response.user.subscription.status,
        };
        localStorage.setItem("user", JSON.stringify(storedUser));
        setUser(storedUser);
        navigate("/account");
      } else {
        setTimeout(() => refreshUser(attempt + 1), 1000);
      }
    });
  };

  useEffect(() => {
    if (user && ["trialing", "infinite", "active"].indexOf(user.subscription) !== -1) {
      navigate("/account");
      return;
    }

    const payment = searchParams.get('payment');
    if (payment === 'success') {
      const sessionId = searchParams.get('session_id');
      setProcessing(true);
      SubscriptionService.verifyCheckout(sessionId).then(() => {
        setSearchParams({}, { replace: true });
        refreshUser(1);
      });
    } else if (payment === 'cancelled') {
      toast.info(t('payment-cancelled', { ns: 'billing' }));
      setSearchParams({}, { replace: true });
    }

    SubscriptionService.getPlans().then((response) => setPlans(response));
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  const handlePayment = (id) => {
    if (!id) return;
    setProcessing(true);
    SubscriptionService.startCheckout(id).then((response) => {
      if (response && response.checkout_url) {
        // Hand off to Stripe-hosted Checkout.
        window.location.href = response.checkout_url;
      } else {
        toast.error(t(response?.error || 'payment-failed', { ns: 'billing' }));
        setProcessing(false);
      }
    });
  };

  return (
    <>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>{t('plans')}</h2>
          </div>
        </div>
      </header>
      <p>
        <strong>
          <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(showTrial ? t('trial-subscription') : t('normal-subscription')) }} />
        </strong>
      </p>
      { showTrial &&
        <p className="card card-success">
          {t("trial-explanation")}
        </p>
      }
      { processing && <LoaderIndicator /> }
      <Table striped responsive bordered hover>
        <thead>
          <tr>
            <th>{t('label')}</th>
            <th>{t('price')}&nbsp;{t('ttc')}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          { plans && plans.length>0 ? plans.map(
            item =>
            <tr key={item.id}>
              <td>{t(item.label.key)}&nbsp;{showTrial?t('with-trial'):''}</td>
              <td>{item.price}&nbsp;€</td>
              <td>
                <span className="link action" onClick={ () => handlePayment(item.id)}>
                  <button className="btn btn-primary" disabled={processing}>
                    <CardOutline color={null} title={t('proceed-to-payment')} />
                    &nbsp; {showTrial ? t('try') : t('pay')}
                  </button>
                </span>
              </td>
            </tr>
          )
          :
            <tr>
              <td colSpan="3" className="text-center">
                {t('no-plans-for-the-moment')}
              </td>
            </tr>
          }
        </tbody>
      </Table>
    </>
  );
};

export default Subscribe;
