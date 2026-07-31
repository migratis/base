// Refund and right-of-withdrawal policy. The rules themselves come from the
// terms of sale (14-day EU withdrawal); this page restates them where a buyer
// can actually find them, per product: credits, code generation, subscription.
import LegalPage from './LegalPage';

const RefundPolicy = () => (
  <LegalPage
    ns="legal"
    titleKey="refund-policy"
    descriptionKey="refund-policy-intro"
    sections={[
      'refund-withdrawal-right',
      'refund-credits',
      'refund-codegen',
      'refund-subscription',
      'refund-how-to-ask',
    ]}
    updatedKey="legal-updated"
  />
);

export default RefundPolicy;
