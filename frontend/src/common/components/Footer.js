import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import { 
    IoInformationCircleOutline as InformationCircleOutline,
    IoConstructOutline as ConstructOutline,
    IoPersonOutline as PersonOutline
} from 'react-icons/io5';
import DOMPurify from 'dompurify';
import { cguvDocument, rgpdDocument } from "../tools/legalDocuments";
import { GENERATOR } from "../../settings";

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
                <Row>
                    <Col sm={12} lg={4}>
                        <h5>
                            <PersonOutline
                                color={'#ffffff'} 
                                title={t('about')}
                                height="30px"
                                width="30px"
                            />&nbsp;&nbsp;
                            {t('about').toUpperCase()}
                        </h5>
                        <br/>
                        { <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(t('text-about')) }}/> }
                    </Col>
                    <Col className="footer-sm" sm={12} lg={4}>
                        <h5>
                            <ConstructOutline
                                color={'#ffffff'} 
                                title={t('other-services')}
                                height="30px"
                                width="30px"
                            />&nbsp;&nbsp;
                            {t('other-services').toUpperCase()}
                        </h5>
                        <br/>
                        { <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(t('text-other-services')) }}/> }
                    </Col>
                    <Col className="footer-sm" sm={12} lg={4}>
                        <h5>
                            <InformationCircleOutline
                                color={'#ffffff'} 
                                title={t('about')}
                                height="30px"
                                width="30px"
                            />&nbsp;&nbsp;
                            {t('informations').toUpperCase()}
                        </h5>
                        <br/>
                        <p>{t('text-informations')}</p>
                        {/* Two columns of links inside the pane: getting help on
                            one side, the legal set on the other. Flat, they ran
                            to eleven lines and buried the support entry. */}
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
                                { GENERATOR &&
                                    <NavLink className="foot-link" to={"/licensing"}>
                                        <strong>{t('licensing')}</strong>
                                    </NavLink>
                                }
                                <NavLink className="foot-link" to={"/disclaimer"}>
                                    <strong>{t('legal-disclaimer')}</strong>
                                </NavLink>
                            </nav>
                        </div>
                    </Col>
                </Row>
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