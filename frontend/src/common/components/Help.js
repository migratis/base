// =============================================================================
// Help — the hub the footer's "Help" link has always pointed at without a route
// behind it. Not a knowledge base: a short orientation plus the three places a
// user actually needs (the generator documentation, the agent/API guide, and a
// human), so nobody is left guessing where to go.
// =============================================================================
import { useTranslation } from 'react-i18next';
import { NavLink, useOutletContext } from 'react-router-dom';
import DOMPurify from 'dompurify';
import { PageShell, PagePanel } from './PageShell';
import { LegalSection } from './LegalPage';
import { GENERATOR } from '../../settings';

const Help = () => {
  const { t } = useTranslation('info');
  // Layout publishes the session on the outlet context. The page is public, so
  // there may be none — that only changes where "get in touch" points.
  const { user } = useOutletContext() || {};

  return (
    <PageShell title={t('help')} description={t('help-intro')} panel={false}>
      <PagePanel title={t('help-getting-started-title')}>
        <div
          dangerouslySetInnerHTML={{
            __html: DOMPurify.sanitize(t('help-getting-started')),
          }}
        />
      </PagePanel>

      {GENERATOR && (
        <PagePanel title={t('help-documentation-title')}>
          <div
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(t('help-documentation')),
            }}
          />
          <NavLink className="btn btn-secondary" to="/generator/docs">
            {t('help-open-documentation')}
          </NavLink>
        </PagePanel>
      )}

      <PagePanel>
        <LegalSection t={t} sectionKey="help-credits" />
        <LegalSection t={t} sectionKey="help-account" />
      </PagePanel>

      <PagePanel title={t('help-contact-title')}>
        <div
          dangerouslySetInnerHTML={{
            __html: DOMPurify.sanitize(t('help-contact')),
          }}
        />
        {/* Signed-in users get a ticket with history; visitors get the form. */}
        <NavLink className="btn btn-primary" to={user ? '/support/ticket' : '/contact'}>
          {user ? t('help-open-ticket') : t('help-contact-us')}
        </NavLink>
      </PagePanel>
    </PageShell>
  );
};

export default Help;
