// Security page: how to report a vulnerability, and a plain summary of how the
// platform handles credentials, data and generated code. Deliberately claims
// nothing it cannot back — no certifications, no uptime promises.
import LegalPage from './LegalPage';

const Security = () => (
  <LegalPage
    ns="legal"
    titleKey="security"
    descriptionKey="security-intro"
    sections={[
      'security-report',
      'security-data',
      'security-credentials',
      'security-generated-code',
      'security-no-warranty',
    ]}
    updatedKey="legal-updated"
  />
);

export default Security;
