import api from "../tools/axios";

// Invoices are issued by the shared payment engine for every paying purpose, so
// listing them belongs to neither the credits nor the subscription module: both
// read this service with their own `purpose`, and neither has to import the
// other to show its receipts on Account → Billing.

const getInvoices = (purpose) => {
  const query = purpose ? `?purpose=${encodeURIComponent(purpose)}` : '';
  return api.get(`/billing/invoices${query}`)
    // The shared axios interceptor *resolves* failed requests with the error
    // response (so 401/403 can be handled globally), which means `data` is an
    // error object — `{ detail: 'Unauthorized' }` — as often as it is a list.
    // Anything that is not an array is no invoices.
    .then((response) => (Array.isArray(response.data) ? response.data : []))
    .catch(() => []);
};

const download = (invoice) => {
  return api.get(`/billing/invoice/download/${invoice.id}`, {})
    .then((response) => {
      if (response.data) return response.data;
      else return response;
    });
};

const InvoicesService = {
  getInvoices,
  download,
};

export default InvoicesService;
