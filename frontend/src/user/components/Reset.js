import { useState } from 'react';
import UserService from "../services/user.service";
import { FormProvider, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import InputField from '../../common/fields/InputField';
import { PageShell } from '../../common/components/PageShell';
import { toast } from 'react-toastify';

const Reset = () => {
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState(false);        
  const [serverErrors, setserverErrors] = useState([]);      
  const { t } = useTranslation('reset');
  const methods = useForm();
  const { handleSubmit } = methods;

  const emailPattern = {
    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
    message: t('email-invalid')
  }

  const onSubmit = async (data) => {
      UserService.reset(data).then(
          (response) => {
              if (response.detail[0].success) {
                  setMessage(response.detail[0].success[0]);
                  setSuccess(true);
              } else {
                  if (response.detail[0] && response.detail[0].loc) {
                      var message = {};
                      for (var i=0;i<response.detail.length;i++) {            
                          message[response.detail[i].loc[1]] = t(response.detail[i].msg);                
                      }
                      setserverErrors(message);
                  }
                  toast.error(t('error-occured'));
                  setSuccess(false);
              }
          }
      );
  };
 
  if (success) {
    return (
      <PageShell title={ t('reset-password') } width="form">
        <p className="page-message"><strong>{ t(message) }</strong></p>
      </PageShell>
    );
  } else {
    return (
      <PageShell title={ t('reset-password') } width="form">
        <p className="form-intro">
          {t('fields-mandatory')}
          <span style={{color: 'red'}}>&nbsp;*</span>
        </p>
        <FormProvider {...methods}>
      	  <form onSubmit={ handleSubmit(onSubmit) }>
					  <fieldset className="migratis-fieldset text-left">
            
              <InputField
                name="email"
                label={ t('email') }
                help={ t('help-change-password') }
                required={true}    
                maxLength={255}                
                pattern={emailPattern}
                serverError={serverErrors.email}
              />

              <div className="form-actions">
                <button className="btn btn-primary">{t('validate')}</button>
              </div>
					  </fieldset>
          </form>
        </FormProvider>
      </PageShell>
    );
  }
}
 
export default Reset