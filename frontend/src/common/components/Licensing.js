// Open-source / GPL publication notice. Approving a custom component or a
// sandbox plugin publishes it under the GPL and stamps the notice into its code
// (see backend licensing.py); Article 7 of the terms says so, and this page is
// where an author can read what that actually means before contributing.
import LegalPage from './LegalPage';

const Licensing = () => (
  <LegalPage
    ns="legal"
    titleKey="licensing"
    descriptionKey="licensing-intro"
    sections={[
      'licensing-what-is-published',
      'licensing-what-stays-yours',
      'licensing-obligations',
      'licensing-platform-code',
    ]}
    updatedKey="legal-updated"
  />
);

export default Licensing;
