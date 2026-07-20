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

const createPayment = (data) => {
  return api.get("/subscription/payment/" + data.id, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    } 
  )
};
  
const getInvoices = () => {
  return api.get("/subscription/invoices", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const download = (invoice) => {
  return api.get("/subscription/invoice/download/" + invoice.id, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

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

const getTax = (id) => {
  return api.get("/subscription/tax/" + id, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  ).catch( (error) => {
    // A Stripe failure while materialising the customer (e.g. a refused tax
    // number) comes back as a 422 { detail: [{ msg }] }. Surface the specific
    // key so the payment form toasts the real reason instead of a generic one.
    if (error.response && error.response.status === 422) {
      const detail = error.response.data && error.response.data.detail;
      return { error: detail && detail[0] ? detail[0].msg : "no-customer" };
    }
    return { error: "no-customer" };
  });
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
  createPayment,
  getInvoices,
  download,
  unsubscribe,
  resubscribe,
  getTax,
  changePlan
}
  
export default SubscriptionService;