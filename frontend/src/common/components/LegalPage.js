// =============================================================================
// LegalPage — the shared shape of every static policy page in the footer.
//
// Legal notice, refund policy, licensing, security and the disclaimer are all
// the same object: a title and an ordered run of (heading, HTML body) sections
// whose text lives entirely in a translation namespace. Rolling each of them by
// hand meant five near-identical files drifting apart, and it is exactly the
// sort of content that must read the same in all four languages.
//
//   <LegalPage ns="legal" titleKey="legal-notice" sections={[
//     'legal-notice-publisher', 'legal-notice-host',
//   ]} />
//
// A section key `x` renders `t('x-title')` as the heading and `t('x')` as the
// body. The body is HTML (paragraphs, lists, links) so a translator can shape a
// clause properly — it goes through DOMPurify because the text is data, read
// from the database at runtime, not a literal in this bundle.
// =============================================================================
import { useTranslation } from 'react-i18next';
import DOMPurify from 'dompurify';
import { PageShell } from './PageShell';

export const LegalSection = ({ t, sectionKey }) => (
  <section className="legal-section">
    <h2 className="legal-section-title">{t(`${sectionKey}-title`)}</h2>
    <div
      className="legal-section-body"
      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(t(sectionKey)) }}
    />
  </section>
);

const LegalPage = ({ ns, titleKey, descriptionKey, sections, updatedKey, children }) => {
  const { t } = useTranslation(ns);

  return (
    <PageShell
      title={t(titleKey)}
      description={descriptionKey ? t(descriptionKey) : undefined}
    >
      {sections.map((sectionKey) => (
        <LegalSection key={sectionKey} t={t} sectionKey={sectionKey} />
      ))}
      {children}
      {updatedKey && <p className="legal-updated">{t(updatedKey)}</p>}
    </PageShell>
  );
};

export default LegalPage;
