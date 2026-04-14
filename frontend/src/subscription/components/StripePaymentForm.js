import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import SubscriptionService from '../services/subscription.service';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import {
  Elements,  
  CardElement,
  useElements,
  useStripe
} from "@stripe/react-stripe-js";
import { STRIPE_API_KEY } from "../../settings";
import { loadStripe } from "@stripe/stripe-js";
import stripe_power from '../../img/powered_by_stripe.png';
import cards from '../../img/card_logos_medium.png';
import logo from '../../img/logo.png'
import { useAuth } from "../../user/hooks/useAuth";
import { toast } from 'react-toastify';
import { useNavigate } from "react-router-dom";

const stripePromise = loadStripe(STRIPE_API_KEY); 

const PaymentForm = (props) => {
  const { t } = useTranslation('subscription');
  const stripe = useStripe();
  const elements = useElements();
  const [ disableSubmit, setDisableSubmit ] = useState(false);  
  const { user } = useAuth();
  const [ stripeError, setStripeError ] = useState(null);
  const [ tax, setTax ] = useState({ amount: 0, rate: 0 });
  const navigate = useNavigate();

  useEffect(() => {
    SubscriptionService.getTax(props.plan.id).then(
        (response) => {
          if (response.error) {
            toast.error(t(response.error));
            navigate("/profile");
          } else {
            setTax(response.tax);
          }
        }
    );
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = (plan) => async () => {
    setDisableSubmit(true);
    setStripeError(null); 
    const cardElement = elements.getElement(CardElement);
    const {error, paymentMethod} = await stripe.createPaymentMethod({
      type: 'card',
      card: cardElement    
    });
    if (error) {
      setStripeError(error.message);
      setDisableSubmit(false);
    } else {
      SubscriptionService.createPayment(plan).then(
        (response) => {
          if (response.clientSecret) {
            if (user.trial) {
              stripe.confirmCardSetup(response.clientSecret, {
                payment_method: paymentMethod.id
              }).then((result) => {
                if (result.error) {
                  setStripeError(result.error.message);              
                  setDisableSubmit(false);
                  return false;
                } else {
                  toast.success(t('subscription-success'));
                  props.closePaymentModal();
                  return true;
                }
              });
            } else {
              stripe.confirmCardPayment(response.clientSecret, {
                payment_method: paymentMethod.id,
                setup_future_usage: 'off_session'
              }).then((result) => {
                if (result.error) {
                  setStripeError(result.error.message);              
                  setDisableSubmit(false);
                  return false;
                } else {
                  toast.success(t('subscription-success'));
                  props.closePaymentModal();
                  return true;
                }
              });
            }
          } else if (response.paid) {
            toast.success(t('subscription-success'));
            props.closePaymentModal();
            return true;          
          } else {
            toast.error(t('subscription-error'));
            if (response.detail && response.detail[0] && response.detail[0].loc) {
              setStripeError(t(response.detail[0].msg));
            } else {
              setStripeError(response.data);  
            }            
            setDisableSubmit(false);
            return false;
          }
        }
      );
    }
  };
  
  return (
    <>     
      <Container>
        <Row>
          <Col sm={12} lg={4}>
            <Container className="payment-info h-100"> 
              <Row>
                <Col sm={12} lg={12} className="text-left">
                  <img alt="Simple Projection" src={logo} />
                </Col>             
              </Row>      
              <Row>
                <Col sm={12} lg={12} className="text-left">
                  <hr />
                </Col>             
              </Row>              
              <Row>
                <Col sm={12} lg={4} className="text-left">
                    <strong>
                      {t('plan')}                      
                    </strong>
                </Col>
                <Col sm={12} lg={8} className="text-left">
                    {t(props.plan.label.key)}
                </Col>                
              </Row>
              <Row>
                <Col sm={12} lg={4} className="text-left">
                    <strong>
                      {t('price')}                      
                    </strong>
                </Col>
                <Col sm={12} lg={8} className="text-left">
                    {props.plan.price}&nbsp;€&nbsp;{t('ttc')}
                </Col>                
              </Row>
              <Row>
                <Col sm={12} lg={4} className="text-left">
                  <strong>
                    {t('vat')}                      
                  </strong>
                </Col>
                <Col sm={12} lg={8} className="text-left">
                  { tax &&
                    <>
                      {tax.amount/100}&nbsp;€&nbsp;({tax.rate}%)
                    </>
                  }
                </Col>                
              </Row>
            </Container>
          </Col>
          <Col sm={12} lg={8}>
            <Container>
              <Row>
                <Col sm={12} lg={12} className="text-center">
                  <br/>
                  <img alt={t('stripe-powered')} src={stripe_power} />
                </Col>
              </Row>
              <br/><br/>        
              <Row>
                <Col sm={12} lg={12} className="text-center">
                  <img alt={t('accepted-cards')} src={cards} />
                </Col>
              </Row>
              <br/><br/>        
              <Row>                              
                <Col sm={12} lg={12} className="text-center">
                  <CardElement options={{ hidePostalCode: true }}/>
                  <small className="form-text text-danger">
                    { stripeError ?? stripeError }                                     
                  </small> 
                </Col>
              </Row>
              <br/><br/>
              <Row>
                <Col sm={12} lg={12} className="text-center">
                  <button 
                    className={"btn btn-primary"}
                    disabled={disableSubmit} 
                    onClick={handleSubmit(props.plan, props.closePaymentModal)}
                  >
                    {user.trial ? t('try') : t('pay') }
                  </button>
                </Col>
              </Row> 
            </Container>
          </Col>          
        </Row>      
      </Container>

    </>
  );
}

const StripePaymentForm  = (props) => ( 
  <Elements stripe={stripePromise}>
    <PaymentForm {...props}/>
  </Elements>
);

export default StripePaymentForm;
