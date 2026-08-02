import { useState, useEffect } from "react";
import SelectField from '../../common/fields/SelectField';
import {
  CommonModal as ConfirmationModal,
  CommonModal as ChangeModal
} from "../../common/modals/CommonModal";
import SubscriptionService from '../services/subscription.service';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import moment from 'moment';
import { IoCardOutline as CardOutline } from 'react-icons/io5';
import { useNavigate } from 'react-router-dom';

export const Subscription = (props) => {
  const { t } = useTranslation(['subscription', 'billing']);
  const navigate = useNavigate();
  const [ confirmationModalShow, setConfirmationModalShow ] = useState(false);
  const [ changeModalShow, setChangeModalShow ] = useState(false);
  const [ disableSubmit, setDisableSubmit ] = useState(false);
  const [ subscription, setSubscription ] = useState(props.subscription);
  const [ selectablePlans, setSelectablePlans ] = useState([]);
  const [ planSelected, setPlanSelected ] = useState(null);
  const [ wait, setWait ] = useState(true);
  //const subscriptionChangeable = ["active", "pause"]

  // `useState(props.subscription)` only seeds the initial value; the profile is
  // fetched asynchronously by the parent, so without re-syncing here the tab
  // would stay on "no subscription" forever even once the active plan loads.
  useEffect(() => {
    setSubscription(props.subscription);
  }, [props.subscription]);

  // Selectable upgrade/downgrade plans depend on the (async) current plan.
  useEffect(() => {
    if (subscription && subscription.access && subscription.plan) {
      setWait(true);
      SubscriptionService.getPlans().then((response) => {
        const plans = response
          .filter((item) => item.id !== subscription.plan.id)
          .map((item) => ({ value: item.id, label: t(item.label.key) + " (" + item.price + "€)" }));
        setSelectablePlans(plans);
        setWait(false);
      });
    }
  }, [subscription]);// eslint-disable-line react-hooks/exhaustive-deps

  const handleChangePlan= (id) => {
    setDisableSubmit(true);
    SubscriptionService.changePlan(id).then(
      (response) => {
        if (response.details[0].success) {
          toast.success(t(response.details[0].success[0]));
          setChangeModalShow(false);
          subscription.changed = true;
          props.setSubscription(subscription)
          setSubscription(subscription);
          setDisableSubmit(false);
          // Proration on an upgrade is auto-charged by Stripe to the payment
          // method saved at checkout — no in-app card re-entry needed.
        } else {
          setDisableSubmit(false);
          toast.error(t(response.detail[0].msg));
        }
    });
  }

  const handleUnsubscribe = () => {
    setDisableSubmit(true);
    SubscriptionService.unsubscribe().then(
      (response) => {
        if (response.success) {
          toast.success(t(response.success));  
          setConfirmationModalShow(false);
          subscription.cancelled = true;
          props.setSubscription(subscription)
          setSubscription(subscription);         
          setDisableSubmit(false);
        } else {
          setDisableSubmit(false);
          toast.error(t(response.detail[0].msg));
        }
    });
  }

  const handleReactivate = () => {
    setDisableSubmit(true);
    SubscriptionService.resubscribe().then(
      (response) => {
        if (response.success) {
          toast.success(t(response.success));
          setConfirmationModalShow(false);
          subscription.cancelled = false;
          props.setSubscription(subscription)          
          setSubscription(subscription);            
          setDisableSubmit(false);
        } else {
          setDisableSubmit(false);
          toast.error(t(response.detail[0].msg));
        }
    });
  }

  return (
    <div className="subscription">
      { (!subscription || !subscription.access) ?       
        <>
          <h5>{t('no-subscription')}</h5>
          <br/><br/>
          <button className="btn btn-primary" onClick={() => navigate('/subscribe')}>
            {t('subscribe')}
            &nbsp;<CardOutline color={'#ffffff'} title={t('subscribe')} height="25px" width="25px"/>
          </button>
        </>
        :
        <>       
          <h5>{t('your-subscription')}</h5>
          <br/>
          { subscription && subscription.status === "trialing" && 
            <strong>
              {t("trial-period")}<br/>
            </strong>
          }
          <br/>                    
          <strong>{subscription.cancelled ? 
            t('cancelled-subscription') : 
            t('current-subscription') }:
          </strong>&nbsp;{t(subscription.plan.label.key)}&nbsp;{subscription.plan.price}&euro;
          <br/>
          { subscription && subscription.status !== "infinite" &&
            <>
              <strong>{subscription.cancelled ?
                t('access-until') : 
                ((subscription.status === "trialing") ? 
                t('first-payment-at') :
                t('automatic-renewal-at')) }:
              </strong>
              &nbsp;{moment(subscription.end).format('DD-MM-y HH:mm:ss')}
              <br/><br/>        
              <button className="btn btn-primary" onClick={() => setConfirmationModalShow(true)}>
                { subscription.cancelled ? t('reactivate-subscription') : t('unsubscribe')}
              </button>

              { subscription.status !== "trialing" &&
                <>
                  <br/><br/>    
                  <button className="btn btn-primary" onClick={() => setChangeModalShow(true)}>
                    {t('change-subscription')}
                  </button>
                </>
              }
            </>
          }
          <ConfirmationModal
            show={confirmationModalShow}
            onHide={() => setConfirmationModalShow(false)}
            title={subscription.cancelled ? t('reactivate-subscription') : t('unsubscribe')}
          >
            <div className="text-center">
              {subscription.cancelled ? t('confirm-reactivate-subscription') : t('confirm-unsubscribe')}
              <br/><br/>
              <small className="form-text text-muted">
                {subscription.cancelled ? t('help-confirm-reactivate-subscription') : t('help-confirm-unsubscribe')}                                  
              </small>
              <br/><br/>
              <button className="nav-item btn btn-danger w-50" disabled={disableSubmit} onClick={subscription.cancelled ? () => handleReactivate() : () => handleUnsubscribe()}>
                {t('validate')}
              </button>
            </div>        
          </ConfirmationModal>
          {!wait && 
          <ChangeModal
            show={changeModalShow}
            onHide={() => setChangeModalShow(false)}
            title={t('change-subscription')}
          >
            <div className="text-center">
              {t('confirm-change-subscription')}
              <br/><br/>
              <small className="form-text text-muted">
                {t('help-change-subscription')}                                  
              </small>
              <br/><br/>
              <SelectField
                value={planSelected}
                placeholder={t('select-plan') + `...`}
                options={selectablePlans}
                onChange={(item) => setPlanSelected(item)}
              />
              <br/><br/>
              <button className="nav-item btn btn-danger w-50" disabled={disableSubmit} onClick={() => handleChangePlan(planSelected.value)}>
                {t('validate')}
              </button>
            </div>        
          </ChangeModal>
          }
        </>
      }

      {/* Invoices are no longer listed here: Account → Billing shows credits and
          subscription side by side, each column listing its own receipts
          through common/components/InvoiceList. */}
    </div>
  );
}