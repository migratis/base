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
  );
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