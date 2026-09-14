import Container from 'react-bootstrap/Container';
import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import { cguvDocument, rgpdDocument } from "../tools/legalDocuments";
// `flag()` rather than an import: a deployment of this template may not declare
// a module's flag at all, and webpack rejects a static read of an export that
// does not exist — whether it is reached by name or through a namespace.
import { flag } from "../tools/featureFlag";

/**
 * The base template's footer, and the ONE file under `common/` that migratis
 * does not sync down.
 *
 * migratis.ai's own footer publishes migratis.ai's terms of sale, privacy
 * policy, refund policy, legal notice and security statement. An application
 * built from this template is owned, hosted and operated by somebody else, and
 * a byte-copy of that footer had it publishing another company's legal
 * documents as its own — in four languages, under its own domain, linked from
 * every page. That is not a styling difference; it is the wrong publisher's
 * name on a binding document. So `.claude/settings.json`'s sync hook skips
 * `common/components/Footer.js`, and this file is base's to edit.
 *
 * What is left is what is honestly ours to say — the framework this runs on and
 * where its source lives — plus the documents that belong to whoever runs this.
 * Everything migratis.ai publishes *about itself* (its refund policy, its legal
 * notice, its security statement, its service status, its help) is gone, and
 * its absence is the right place for an operator to notice what they still owe
 * their own users.
 *
 * Three links are this deployment's own document rather than Migratis':
 *
 *   - the terms of sale and the privacy policy, which `docs/legal/*.html`
 *     renders into `frontend/src/documents/*.pdf`. What ships there is a
 *     placeholder that says so — the terms of a service can only be written by
 *     the person who operates it — and it is linked here for the same reason
 *     the registration form links it: a document nobody can reach is a document
 *     nobody notices is missing.
 *   - `/cookies`, which is not about Migratis at all: this deployment's own
 *     cookie table, filled from its own database by `manage.py seed_cookies`.
 *     It is a module a deployment may or may not carry, so the link follows the
 *     flag — and because `COOKIE` is one flag for the whole deployment rather
 *     than one per installed application, two installed applications that both
 *     use it still produce exactly one link.
 */

// The published version of the application, shown in the footer's bottom line.
const VERSION = 'v1.0';

// Where a reader goes to find out what this is built with, and to read the
// framework's own source. Constants rather than inline strings: they are the
// only two addresses this file exists to carry.
const MIGRATIS_URL = 'https://migratis.ai';
const SOURCE_URL   = 'https://github.com/migratis/base';

export const Footer = () => {
    const { t, i18n } = useTranslation('layout');
    const cguv = cguvDocument(i18n.language);
    const rgpd = rgpdDocument(i18n.language);

    return (

        <footer>
            <Container>
                <nav className="footer-generic" aria-label={t('informations')}>
                    <NavLink target="_blank" className="foot-link" to={cguv}>
                        <strong>{t('terms-of-service')}</strong>
                    </NavLink>
                    <NavLink target="_blank" className="foot-link" to={rgpd}>
                        <strong>{t('privacy-policy')}</strong>
                    </NavLink>
                    { flag('COOKIE') &&
                        <NavLink className="foot-link" to={"/cookies"}>
                            <strong>{t('cookies')}</strong>
                        </NavLink>
                    }
                    {/* `<a>`, not `<NavLink>`: these leave the application. */}
                    <a className="foot-link" href={MIGRATIS_URL}
                       target="_blank" rel="noreferrer">
                        <strong>{t('built-with-migratis')}</strong>
                    </a>
                    <a className="foot-link" href={SOURCE_URL}
                       target="_blank" rel="noreferrer">
                        <strong>{t('source-code')}</strong>
                    </a>
                </nav>
                <div className="footer-bottom">
                    {VERSION}
                </div>
            </Container>
        </footer>

    );

}
