import CookieConsent from "react-cookie-consent";
import { useTranslation } from 'react-i18next';

export const SPCookieConsent = () => {
    const { t } = useTranslation('layout');
        
        return (
            <div className="consent">            
            <CookieConsent
                location="bottom"
                buttonText={t('accept')}
                cookieName="spcc1"
                style={{ zIndex: "1102 !important", background: "#96a4d2" }}
                buttonStyle={{ background: "#77b15f", color: "#ffffff"}}
                expires={150}
                overlay={true}
            >
                {t('cookie-consent-text')}&nbsp;<a href="/cookies">{t('explore-cookies')}</a>
            </CookieConsent>
            </div>
        );
}