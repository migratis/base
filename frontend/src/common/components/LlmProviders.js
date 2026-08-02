// =============================================================================
// LlmProviders — an open invitation to model providers who are not in the
// catalog yet.
//
// The generator's model picker is a database catalog (generator.LLMProvider /
// LLMModel), not a fixed list in the code: a provider that speaks the
// OpenAI-compatible protocol and publishes its rates can be added without a
// release. Nothing said so anywhere a provider would look, so the only route in
// was knowing someone. This page states the terms — the protocol, the key, the
// published price list, the verification rule — and points at the contact form.
//
// Generator-gated (see the route and the footer link): a deployment without a
// model picker has nothing to be listed in.
// =============================================================================
import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import LegalPage from './LegalPage';

const LlmProviders = () => {
  const { t } = useTranslation('info');

  return (
    <LegalPage
      ns="info"
      titleKey="llm-providers"
      descriptionKey="llm-providers-intro"
      sections={[
        'llm-providers-catalog',
        'llm-providers-requirements',
        'llm-providers-pricing',
        'llm-providers-contact',
      ]}
    >
      {/* The page is public and its readers are outsiders, so it points at the
          contact form rather than the signed-in ticket list. */}
      <NavLink className="btn btn-primary" to="/contact">
        {t('llm-providers-get-listed')}
      </NavLink>
    </LegalPage>
  );
};

export default LlmProviders;
