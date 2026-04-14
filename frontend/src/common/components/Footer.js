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
import cguv from "../../documents/cguv.txt";
import rgpd from "../../documents/rgpd.txt";

export const Footer = (props) => {
    const { t } = useTranslation('layout');

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
                        <NavLink className="foot-link" to={props.user ? "/support/ticket" : "/contact"}>
                            <strong>{props.user ? t('support') : t('contact')}</strong>
                        </NavLink>
                        <br/>
                        <NavLink className="foot-link" to={'/help'}>
                            <strong>{t('help')}</strong>
                        </NavLink>
                        <br/>
                        <NavLink target="_blank" className="foot-link" to={cguv}>
                            <strong>{t('terms-of-service')}</strong>
                        </NavLink> 
                        <br/>
                        <NavLink target="_blank" className="foot-link" to={rgpd}>
                            <strong>{t('privacy-policy')}</strong>
                        </NavLink> 
                        <br/>                                              
                        <NavLink className="foot-link" to={"/disclaimer"}>
                            <strong>{t('legal-disclaimer')}</strong>
                        </NavLink>                                                                                  
                    </Col>                    
                </Row>
                <br/><br/>
                <Row>
                    <Col sm={12} lg={12}>
                        <div  className="text-center">
                            v1.2 - {t('all-rights-reserved')}
                        </div>
                    </Col>
                </Row>
            </Container>
        </footer>

    );

}