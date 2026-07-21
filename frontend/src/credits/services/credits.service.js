import api from "../../common/tools/axios";

// Credit balance / metered-billing service. Standalone (no generator import) so
// the `credits` module can be activated on its own — e.g. shipped into base as
// an additional feature alongside subscription/support.

const getCallCosts = () => {
  return api.get('/credits/costs')
    .then((response) => response.data || {});
};

const getCredits = () => {
  return api.get('/credits/balance')
    .then((response) => {
      if (response.data) return response.data;
      else return response;
    });
};

const getCreditsTiers = () => {
  return api.get('/credits/tiers')
    .then((response) => {
      if (response.data) return response.data;
      else return response;
    });
};

const purchaseExtraCalls = (tierIndex, customQuantity = null) => {
  // Unified payment engine: a one-off Checkout Session for credits.
  const params = new URLSearchParams({ purpose: 'credits', tier_index: tierIndex });
  if (customQuantity) {
    params.append('custom_quantity', customQuantity);
  }
  return api.post(`/billing/checkout?${params.toString()}`)
    .then((response) => {
      if (response.data) return response.data;
      else return response;
    })
    .catch((error) => {
      // Surface the specific reason (422 { detail: [{ msg }] }); the modal
      // toasts it from the shared 'billing' namespace.
      if (error.response && error.response.status === 422) {
        const detail = error.response.data && error.response.data.detail;
        return { error: detail && detail[0] ? detail[0].msg : 'payment-failed' };
      }
      return { error: 'payment-failed' };
    });
};

const CreditsService = {
  getCallCosts,
  getCredits,
  getCreditsTiers,
  purchaseExtraCalls,
};

export default CreditsService;
