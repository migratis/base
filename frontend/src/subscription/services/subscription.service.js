import api from "../../common/tools/axios";
import qs from 'qs';

const getPlans = () => {
  return api.get("/subscription/plans", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

// Unified payment engine: subscribing starts a hosted Checkout Session and
// redirects; the return page confirms via verifyCheckout.
const startCheckout = (planId) => {
  const params = new URLSearchParams({ purpose: 'subscription', plan_id: planId });
  return api.post(`/billing/checkout?${params.toString()}`)
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    })
    .catch( (error) => {
      if (error.response && error.response.status === 422) {
        const detail = error.response.data && error.response.data.detail;
        return { error: detail && detail[0] ? detail[0].msg : 'payment-failed' };
      }
      return { error: 'payment-failed' };
    });
};

const verifyCheckout = (sessionId) => {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return api.get(`/billing/checkout/verify${params}`)
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    });
};
  
// NOTE: invoice listing / download moved to common/services/invoices.service.js
// — receipts are issued by the shared payment engine for every paying purpose,
// so the credits module lists its own without importing this one.

const unsubscribe = () => {
  return api.get("/subscription/unsubscribe", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    } 
  )
};  

const resubscribe = () => {
  return api.get("/subscription/resubscribe", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    } 
  )
};

const changePlan = (id) => {
  return api.post("/subscription/change", qs.stringify(
    { 
      id: id 
    }),
    { 
      headers: {
        'content-type': 'application/x-www-form-urlencoded'
      }
    }
  ).then( (response) => {
    if (response.data) return response.data;
    else return response;
  }).catch( (error) => {
    if (error.response.status === 422) {
      return error.response.data;
    } 
  });
}; 

const SubscriptionService = {
  getPlans,
  startCheckout,
  verifyCheckout,
  unsubscribe,
  resubscribe,
  changePlan
}
  
export default SubscriptionService;