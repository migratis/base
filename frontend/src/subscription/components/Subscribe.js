import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import SubscriptionService from '../services/subscription.service';
import Table from 'react-bootstrap/Table';
import { 
  IoCardOutline as CardOutline,
  IoLockClosedOutline as LockClosedOutline 
} from 'react-icons/io5';
import { toast } from 'react-toastify';
import { CommonModal } from '../../common/modals/CommonModal';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';
import DOMPurify from 'dompurify';
import StripePaymentForm from "./StripePaymentForm";
import UserService from "../../user/services/user.service";
import { useOutletContext } from "react-router-dom";
import { useNavigate } from "react-router-dom";

const Subscribe = () => {
  const { t } = useTranslation('subscription');
  // eslint-disable-next-line
  const { user, setUser } = useOutletContext(); 
  const [ plans, setPlans ] = useState([]);
  const [ planId, setPlanId ] = useState(null);
  const [ paymentModalShow, setPaymentModalShow ] = useState(false);
  const [ subscription, setSubscription ] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {

    if ((user && ["trialing", "infinite", "active"].indexOf(user.subscription) !== -1) || (subscription && subscription.access)) {
      navigate("/account");
    }

    SubscriptionService.getPlans().then(
        (response) => {
          setPlans(response);
        }
    );
  }, []);// eslint-disable-line react-hooks/exhaustive-deps
  
  const handlePayment = (id) => {
    if (id) {
        setPlanId(id);
        setPaymentModalShow(true);
    }
  };

  const refreshUser = (attempt) => {
    if (attempt < 5) {
      UserService.refreshUser().then(
        (response) => {
          if (response.user && response.user.subscription && response.user.subscription.access) { 
            const storedUser = {
              id: response.user.id,
              trial: response.user.trial,
              subscription: response.user.subscription.status
            };
            localStorage.setItem("user", JSON.stringify(storedUser));
            setUser(storedUser);
            setSubscription(response.user.subscription);
            setPaymentModalShow(false);
            navigate("/account");
          } else {
            setTimeout(refreshUser(1), 1000);
          }
        }
      );
    } else {
      toast.error(t('subscription-error'));
    }
  };

  const closePaymentModal = () => {
    setTimeout(refreshUser(1), 1000); 
  }  

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
          <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(user && user.trial ? t('trial-subscription') : t('normal-subscription')) }} />
        </strong>
      </p>
      { user && user.trial &&
        <p className="card card-success">
          {t("trial-explanation")}
        </p>
      }
      <LoaderIndicator />
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
              <td>{t(item.label.key)}&nbsp;{user && user.trial?t('with-trial'):''}</td>
              <td>{item.price}&nbsp;€</td>
              <td> 
                <span className="link action" onClick={ () => handlePayment(item.id)}>
                  <button className="btn btn-primary">
                    <CardOutline color={null} title={t('proceed-to-payment')} />
                    &nbsp; {user && user.trial ? t('try') : t('pay')}
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
      <CommonModal
        show={paymentModalShow}
        onHide={() => setPaymentModalShow(false)}
        icon={<LockClosedOutline color={'#ffffff'} title={t('secure-zone')} />}
        title={t('secure-payment')}
        nocontainer="true"
      >
        <StripePaymentForm 
          plan={plans.find((item) => { return item.id === planId })}
          trial={user.trial}
          closePaymentModal={closePaymentModal}
        />
      </CommonModal>
    </>
  );
}; 

export default Subscribe;
