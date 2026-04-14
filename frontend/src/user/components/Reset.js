import { useState } from 'react';
import UserService from "../services/user.service";
import { FormProvider, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import InputField from '../../common/fields/InputField';
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
      <>
        <header className="sticky-top">
          <div className="row">
            <div className="col-sm-12">
              <h2>{ t('reset-password') }</h2>
            </div>
        	</div>
        </header>
        <p><strong>{ t(message) }</strong></p>
      </>        
    );
  } else {
    return (
      <>
        <header className="sticky-top">
          <div className="row">
            <div className="col-sm-12">
              <h2>{ t('reset-password') }</h2>
            </div>
          </div>
        </header>            
        <p className="text-center">
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

              <div className="migratis-field text-center">
                <button className="btn btn-primary btn-block">{t('validate')}</button>
              </div>
					  </fieldset>
          </form>
        </FormProvider>
      </>
    );
  }
}
 
export default Reset