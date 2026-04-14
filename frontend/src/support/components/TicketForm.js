import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import SupportService from '../services/support.service'
import { FormProvider, useForm } from 'react-hook-form';
import { toast } from 'react-toastify';
import InputField from '../../common/fields/InputField';
import SelectField from '../../common/fields/SelectField';
import TextareaField from '../../common/fields/TextareaField';
import  { LoaderIndicator } from '../../common/components/LoaderIndicator';

const TicketForm = (props) => {
  const { t } = useTranslation('support');
  const [ topics, setTopics ] = useState([]); 
  const [ serverErrors, setServerErrors ] = useState({});    
  const [ disableSubmit, setDisableSubmit ] = useState(false);  
  const [ other, setOther] = useState(false);
  const [ topic, setTopic] = useState(props.ticket.topic?{
    value: props.ticket.topic.id,
    label: t(props.ticket.topic.label.key)
  }:props.ticket.object ?{
    value: 0,
    label: t("other-topic") + "..."
  }: null);
  const methods = useForm({
    defaultValues: {
      topic_id: topic?topic:{
        value: 0,
        label: t("other-topic") + "..."
      },
      object: props.ticket?.object,
      content: props.ticket?.content
    }
  }); 
  const { handleSubmit, reset } = methods;

  useEffect(() => {
    SupportService.getTopics().then(
        (response) => {
          const topic_list = [];
          response.forEach(element => {
            topic_list.push({ 
              value: element.id, 
              label: t(element.label.key) 
            })
          });
          topic_list.push({
            value: 0,
            label: t("other-topic") + "..."
          });
          setTopics(topic_list);
        }   
    );
    
    if (!props.ticket.topic && props.ticket.object) {
      setTopic({
        value: 0,
        label: t("other-topic") + "..."
      });
      reset({ topic_id: {
        value: 0,
        label: t("other-topic") + "..."
      }})
      setOther(true);
    } else {
      setTopic(props.ticket.topic);
      setOther(false);
    }
    if (props.ticket) {
      reset({      
        topic_id: topic,
        object: props.ticket.object,
        content: props.ticket.content
      });
    }

  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (topic?.value === 0) {
      setOther(true);
    } else {
      setOther(false);
    }
  }, [topic]);

  const onSubmit = async (data) => {
    if (props.ticket.id) {
      data.id = props.ticket.id;
    }
    setDisableSubmit(true);
    data.topic_id = data.topic_id.value;
    data.language = localStorage.getItem('i18nextLng');
    SupportService.saveTicket(data).then(
      (response) => {
        setDisableSubmit(false);
        if (response.detail[0].success) {
          toast.success(t(response.detail[0].success[0]));
          props.closeAndUpdate(data.id)
        } else {
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
      <LoaderIndicator/>
      <FormProvider {...methods}>
        <form onSubmit={ handleSubmit(onSubmit) }>
          <fieldset className="migratis-fieldset">

            <SelectField          
              name="topic_id"
              label={ t('topic') }
              placeholder={t('select-topic') + `...`}
              required={true}
              options={topics}
              serverError={serverErrors.topic_id}
              dispatch={setTopic}
              isSearchable={true}
            />

            <InputField
              name="object"
              label={ t('free-topic') }
              required={other}
              maxLength={50}
              serverError={serverErrors.object}
              isVisible={other}
            />

            <TextareaField
              name="content"
              label={ t('content') }
              required={true}  
              maxLength={5000}             
              rows={2}             
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

    </>
  );
};

export default TicketForm;
