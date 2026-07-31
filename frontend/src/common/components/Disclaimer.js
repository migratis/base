// Legal disclaimer — the limits of what the platform promises. Publisher and
// host identity moved to the Legal notice page (/legal-notice), which Article 2
// of the terms of sale points at; this page is only about liability and
// warranty, so the two no longer restate each other.
import LegalPage from './LegalPage';

const Disclaimer = () => (
  <LegalPage
    ns="legal"
    titleKey="legal-disclaimer"
    descriptionKey="legal-disclaimer-intro"
    sections={[
      'disclaimer-availability',
      'disclaimer-generated-output',
      'disclaimer-ai-content',
      'disclaimer-external-links',
      'disclaimer-illustrations',
    ]}
    updatedKey="legal-updated"
  />
);

export default Disclaimer;
