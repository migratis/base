import { useState, useEffect } from "react";
import { CommonModal as ConfirmationModal } from "../../common/modals/CommonModal";
import { useTranslation } from 'react-i18next';

export const Reactivate = (props) => {
    const { t } = useTranslation('subscription');
    const [ confirmationModalShow, setConfirmationModalShow ] = useState(false);
    const [ disableSubmit, setDisableSubmit ] = useState(false); 

    useEffect(() => {
        return () => {};
      }, []);

    return (
        <>
            <a className="nav-link">
                <button className={props.class} onClick={() => setConfirmationModalShow(true)}>
                    {t('reactivate-subscription')}
                </button>
            </a>
            <ConfirmationModal
                show={confirmationModalShow}
                onHide={() => setConfirmationModalShow(false)}
                title={t('reactivate-subscription')}
            >
                <div className="text-center">
                    {t('confirm-reactivate-subscription')}<br/><br/>
                    <small className="form-text text-muted">
                        {t('help-confirm-reactivate-subscription')}                                  
                    </small>
                    <br/><br/>                    
                    <button className="nav-item btn btn-danger w-50" disabled={disableSubmit} onClick={() => handleReactivate()}>
                        {t('validate')}
                    </button>
                </div>        
            </ConfirmationModal>     
        </>
    );  
}