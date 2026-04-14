import { useState, useEffect } from "react";
import { CommonModal } from '../../common/modals/CommonModal';
import { useTranslation } from 'react-i18next';
import SupportService from '../services/support.service'
import { toast } from 'react-toastify';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';


export const UploadFile = (props) => {

  const { t } = useTranslation('upload');
  const [ selectedFile, setSelectedFile ] = useState(false);
  const [ serverErrors, setServerErrors ] = useState([]);  
  const [ disableSubmit, setDisableSubmit ] = useState(false);
  const [ ticket, setTicket ] = useState(props.ticket);

  useEffect(() => {
    if (props.ticket) {
      setTicket(props.ticket);
    }
    if (props.onHide) {
      setServerErrors([]);
    }
  }, [props]);// eslint-disable-line react-hooks/exhaustive-deps

  const handleChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleSubmit = () => {
    setDisableSubmit(true);
    const data = new FormData() 
    data.append('file', selectedFile)
      SupportService.uploadFile(ticket.id, data).then(
        (response) => {
          setDisableSubmit(false);
          if (response.detail[0].success) {
            toast.success(t(response.detail[0].success[0]));
            props.closeAndUpdate(ticket.id);
          } else {
            setDisableSubmit(false);
            if (response.detail[0] && response.detail[0].loc) {
              var message = {};
              for (var i=0;i<response.detail.length;i++) {            
                message[response.detail[i].loc[1]] = t(response.detail[i].msg);                                
              }
              setServerErrors(message);
            }
          toast.error(t('error-occured'));
          }
        }
    );
  };

  return (
    <>
      <CommonModal
        show={props.show}
        onHide={props.onHide}
        title={t('upload-file')}
      >
        <LoaderIndicator />
        <div>
            <br /><br />
            <div className="w-100">
              <label className={serverErrors.file ? 'text-danger' : ''}>
                {t('select-file')}
              </label>
              <small className="form-text text-muted">
                {t('upload-support-help')}                                  
              </small>
              <input 
                type="file" 
                className={`form-control ${ serverErrors.file ? 'is-invalid' : '' }`} 
                name="file" 
                onChange={handleChange} />
              <small className="form-text text-danger">
                { serverErrors.file }                                      
              </small>               
            </div>
            <div className="migratis-field text-center">
              <br/>
              <button onClick={handleSubmit} disabled={disableSubmit} className="btn btn-primary btn-block btn-wide">{t('upload')}</button>
              <br/><br/>
            </div>  
        </div>      
      </CommonModal>
    </>
    );
};