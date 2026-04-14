import { useState, useEffect } from "react";
import SelectField from '../../common/fields/SelectField';
import { 
  CommonModal as ConfirmationModal,
  CommonModal as ChangeModal,
  CommonModal as PaymentModal
} from "../../common/modals/CommonModal";
import SubscriptionService from '../services/subscription.service';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import moment from 'moment';
import { 
  IoCardOutline as CardOutline, 
  IoDownloadOutline as DownloadOutline, 
  IoLockClosedOutline as LockClosedOutline 
} from 'react-icons/io5';
import { useNavigate } from 'react-router-dom';
import Badge from 'react-bootstrap/Badge';
import download from 'downloadjs';
import StripePaymentForm from "./StripePaymentForm";
import { COLOR_LINK } from "../../settings";

export const Subscription = (props) => {
  const { t } = useTranslation('subscription');
  const navigate = useNavigate();
  const [ confirmationModalShow, setConfirmationModalShow ] = useState(false);
  const [ changeModalShow, setChangeModalShow ] = useState(false);  
  const [ disableSubmit, setDisableSubmit ] = useState(false);
  const [ invoices, setInvoices ] = useState([]);
  const [ subscription, setSubscription ] = useState(props.subscription);
  const [ selectablePlans, setSelectablePlans ] = useState([]);
  const [ planSelected, setPlanSelected ] = useState(null);
  const [ wait, setWait ] = useState(true);
  const [ paymentModalShow, setPaymentModalShow ] = useState(false);
  const [ plans, setPlans ] = useState([]);
  const [ planId, setPlanId ] = useState(null);
  //const subscriptionChangeable = ["active", "pause"]

  useEffect(() => {
    SubscriptionService.getInvoices().then(
        (response) => {
          setInvoices(response);
        }
    );
    if (subscription) {
      setWait(true);
      SubscriptionService.getPlans().then(
        (response) => {
          setPlans(response);
          let filterPlans = response.filter(
            (item) => {     
              return (item.id !== subscription.plan.id);
            }
          );
          let selectablePlans = filterPlans.map(
            (item) => {
              return {value: item.id, label: t(item.label.key) + " (" + item.price + "€)"}
            }          
          )
          setSelectablePlans(selectablePlans);
        }
      );
      setWait(false);
    }
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  const closePaymentModal = () => {
    setPaymentModalShow(false);
  }  

  const handleChangePlan= (id) => {
    setDisableSubmit(true);
    setPlanId(id);
    SubscriptionService.changePlan(id).then(
      (response) => {
        if (response.details[0].success) {
          toast.success(t(response.details[0].success[0]));
          setChangeModalShow(false);
          subscription.changed = true;
          props.setSubscription(subscription)          
          setSubscription(subscription);            
          setDisableSubmit(false);
          if (response.details[0].needPayment) setPaymentModalShow(true);
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

  function handleDownload(invoice) {
    SubscriptionService.download(invoice).then(
      (response) => {
        download(new Blob([response]), 'migratis-invoice-' + moment(invoice.mdate).format('DD-MM-y') + '.pdf', "application/pdf");
      }
    );
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
          <br/><br/>
          { invoices.length > 0 && 
            <>
              <h5>{t('your-invoices')}:</h5>
              <br/><br/>
              <div className="invoices">  
              { invoices.map(item => 
                <p key={item.id}>
                  {t(item.plan.label.key)}&nbsp;
                  { item.amount === 0 &&
                    <span>
                      ({t("trial-period")})&nbsp;
                    </span>
                  }
                  {t('of')}&nbsp;
                  {moment(item.mdate).format('DD-MM-y')}&nbsp;
                  {item.amount/100}&euro;
                  &nbsp;&nbsp;
                  <Badge bg={item.status==="paid"?"success":"danger"}>{item.status==="paid"?t('paid'):t('unpaid')}</Badge>&nbsp;&nbsp;
                  { item.status==="paid" &&
                    <button className="link btn btn-white" onClick={() => handleDownload(item)}>
                      <DownloadOutline color={COLOR_LINK} title={t('download-invoice')} height="25px" width="25px"/>
                    </button>
                  } 
                </p>
                )
              }
              </div>
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
          <PaymentModal
            show={paymentModalShow}
            onHide={() => setPaymentModalShow(false)}
            icon={<LockClosedOutline color={'#ffffff'} title={t('secure-zone')} />}
            title={t('secure-payment')}
            nocontainer="true"
          >
            <StripePaymentForm 
              plan={plans.find((item) => { return item.id === planId })}
              trial={false}
              closePaymentModal={closePaymentModal}
            />
          </PaymentModal>
        </>
      } 
    </div>
  );  
}