import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import SupportService from '../services/support.service'
import { FormProvider, useForm } from 'react-hook-form';
import { toast } from 'react-toastify';
import TextareaField from '../../common/fields/TextareaField';

const ThreadForm = (props) => {
  const { t } = useTranslation('support');
  const [ serverErrors, setServerErrors ] = useState({});
  const [ ticket, setTicket ] = useState(props.ticket);  
  const [ thread, setThread ] = useState(props.thread);  
  const methods = useForm({
    defaultValues: {
      id: thread?.id,
      content: thread?.content
    }
  });
  const { handleSubmit } = methods
  const [ disableSubmit, setDisableSubmit ] = useState(false);

  useEffect(() => {
      setTicket(props.ticket);
  }, [props.ticket]);

  useEffect(() => {
    setThread(props.thread);
  }, [props.thread]);

  const onSubmit = async (data) => {
    setDisableSubmit(true);
    SupportService.saveThread(data, ticket.id).then(
      (response) => {
        setDisableSubmit(false);
        if (response.detail[0].success) {
          toast.success(t(response.detail[0].success[0]));
          if (props.closeAndUpdate) {
            props.closeAndUpdate(ticket.id);
          } else {
            props.setRefresh(!props.refresh);
            props.handleAccordion(ticket.id);
            props.setActiveKey(ticket.id);
          }                    
        } else {
          if (response.detail[0] && response.detail[0].loc) {
            var message = {};
            for (var i=0;i<response.detail.length;i++) {            
              message[response.detail[i].loc[1]] = t(response.detail[i].msg);                
            }
            setServerErrors(message);
            toast.error(t('error-occured'));
          } else if (response.detail[0].error) {
            toast.error(t(response.detail[0].error[0]));
          } else {
            toast.error(t('error-occured'));
          }        
        }
      }
    );
  };

  return (
    <FormProvider  {...methods}>
      <form onSubmit={ handleSubmit(onSubmit) }>
        <fieldset className="migratis-fieldset">  

          <TextareaField
            name="content"
            label={ t('content') }
            required={true}               
            maxLength={5000}
            rows={4}             
            serverError={serverErrors.content}
          />

          <div className="migratis-field text-center">
            <br/>
            <button disabled={disableSubmit} className="btn btn-primary btn-block btn-wide">
              {t('validate')}
            </button>
            <br/>
            <br/>            
          </div>

        </fieldset>
      </form>
    </FormProvider>

  );
};

export default ThreadForm;