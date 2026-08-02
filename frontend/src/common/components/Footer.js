import Container from 'react-bootstrap/Container';
import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import { IoInformationCircleOutline as InformationCircleOutline } from 'react-icons/io5';
import { cguvDocument, rgpdDocument } from "../tools/legalDocuments";
// `flag()` rather than an import of GENERATOR: this is common/ code, synced
// into the base template, where a feature module's flag may not be declared at
// all — and webpack rejects a static read of an export that does not exist,
// whether it is named or reached through a namespace. See tools/featureFlag.js.
import { flag } from "../tools/featureFlag";

// The published version of the application, shown in the footer's bottom line.
// A named constant so bumping it is one obvious edit rather than a string
// buried in the markup.
const VERSION = 'v1.0';

export const Footer = (props) => {
    const { t, i18n } = useTranslation('layout');
    const cguv = cguvDocument(i18n.language);
    const rgpd = rgpdDocument(i18n.language);

    return (

        <footer>
            <Container>
                {/* One band, not three columns. "About" and "Services" restated
                    the home page in a place nobody reads prose, and squeezed the
                    links — the only part of a footer anyone comes here for —
                    into a third of the width. The links now have the whole
                    band and lay out in rows across it. */}
                <h5>
                    <InformationCircleOutline
                        color={'#ffffff'}
                        title={t('informations')}
                        height="30px"
                        width="30px"
                    />&nbsp;&nbsp;
                    {t('informations').toUpperCase()}
                </h5>
                <p className="footer-intro">{t('text-informations')}</p>
                {/* Two groups, each a row spanning the band: getting help on one
                    line, the legal set on the next. */}
                <div className="footer-links">
                    <nav className="footer-links-group" aria-label={t('help')}>
                        <NavLink className="foot-link" to={props.user ? "/support/ticket" : "/contact"}>
                            <strong>{props.user ? t('support') : t('contact')}</strong>
                        </NavLink>
                        <NavLink className="foot-link" to={'/help'}>
                            <strong>{t('help')}</strong>
                        </NavLink>
                        <NavLink className="foot-link" to={'/status'}>
                            <strong>{t('status')}</strong>
                        </NavLink>
                        <NavLink className="foot-link" to={'/security'}>
                            <strong>{t('security')}</strong>
                        </NavLink>
                        {/* The invitation to model providers only makes sense
                            where there is a model picker to be listed in. */}
                        { flag('GENERATOR') &&
                            <NavLink className="foot-link" to={'/llm-providers'}>
                                <strong>{t('llm-providers')}</strong>
                            </NavLink>
                        }
                    </nav>
                    <nav className="footer-links-group" aria-label={t('legal')}>
                        <NavLink className="foot-link" to={"/legal-notice"}>
                            <strong>{t('legal-notice')}</strong>
                        </NavLink>
                        <NavLink target="_blank" className="foot-link" to={cguv}>
                            <strong>{t('terms-of-service')}</strong>
                        </NavLink>
                        <NavLink target="_blank" className="foot-link" to={rgpd}>
                            <strong>{t('privacy-policy')}</strong>
                        </NavLink>
                        <NavLink className="foot-link" to={"/refund-policy"}>
                            <strong>{t('refund-policy')}</strong>
                        </NavLink>
                        <NavLink className="foot-link" to={"/cookies"}>
                            <strong>{t('cookies')}</strong>
                        </NavLink>
                        {/* Publishing approved components under the GPL
                            only exists because of the generator. */}
                        { flag('GENERATOR') &&
                            <NavLink className="foot-link" to={"/licensing"}>
                                <strong>{t('licensing')}</strong>
                            </NavLink>
                        }
                        <NavLink className="foot-link" to={"/disclaimer"}>
                            <strong>{t('legal-disclaimer')}</strong>
                        </NavLink>
                    </nav>
                </div>
                {/* Its own band rather than two <br/> and a full-width grid
                    row: it needs a rule above it and room below, and stacked
                    line breaks gave it neither — the line sat flush against the
                    bottom edge and read as clipped. */}
                <div className="footer-bottom">
                    {VERSION} - {t('all-rights-reserved')}
                </div>
            </Container>
        </footer>

    );

}