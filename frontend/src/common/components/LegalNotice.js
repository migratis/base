// Legal notice / imprint. Article 2 of the terms of sale points at this page
// for the publisher and host identity, so it has to exist and stay accurate.
import LegalPage from './LegalPage';

const LegalNotice = () => (
  <LegalPage
    ns="legal"
    titleKey="legal-notice"
    descriptionKey="legal-notice-intro"
    sections={[
      'legal-notice-publisher',
      'legal-notice-editor',
      'legal-notice-host',
      'legal-notice-contact',
      'legal-notice-intellectual-property',
    ]}
    updatedKey="legal-updated"
  />
);

export default LegalNotice;
