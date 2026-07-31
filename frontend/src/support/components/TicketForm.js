import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import SupportService from '../services/support.service'
import { FormProvider, useForm } from 'react-hook-form';
import { toast } from 'react-toastify';
import InputField from '../../common/fields/InputField';
import SelectField from '../../common/fields/SelectField';
import TextareaField from '../../common/fields/TextareaField';
import  { LoaderIndicator } from '../../common/components/LoaderIndicator';

// The "Other topic..." sentinel. It is not a `support.Topic` row — picking it
// means "none of the seeded topics fits", and the backend stores the free text
// the user types into `object` instead of a topic FK.
export const OTHER_TOPIC_VALUE = 0;

const TicketForm = (props) => {
  const { t } = useTranslation('support');
  const otherOption = { value: OTHER_TOPIC_VALUE, label: t("other-topic") + "..." };

  // A ticket carries either a seeded topic or a free-text `object`, never both.
  const ticketTopicOption = props.ticket?.topic
    ? { value: props.ticket.topic.id, label: t(props.ticket.topic.label.key) }
    : props.ticket?.object
      ? otherOption
      : null;   // new ticket — nothing preselected, the placeholder shows

  const [ topics, setTopics ] = useState([]);
  const [ serverErrors, setServerErrors ] = useState({});
  const [ disableSubmit, setDisableSubmit ] = useState(false);
  const [ topic, setTopic] = useState(ticketTopicOption);
  const methods = useForm({
    defaultValues: {
      topic_id: ticketTopicOption,
      object: props.ticket?.object,
      content: props.ticket?.content
    }
  });
  const { handleSubmit, reset } = methods;

  // Derived, not stored: the free-text field is visible exactly while the
  // "Other topic..." sentinel is the current selection.
  const other = topic?.value === OTHER_TOPIC_VALUE;

  useEffect(() => {
    SupportService.getTopics().then(
        (response) => {
          const topic_list = [];
          // The endpoint is public and answers an error body (an object) rather
          // than a list when topics cannot be read — never map over that.
          (Array.isArray(response) ? response : []).forEach(element => {
            topic_list.push({
              value: element.id,
              label: t(element.label.key)
            })
          });
          topic_list.push(otherOption);
          setTopics(topic_list);
        }
    );

    reset({
      topic_id: ticketTopicOption,
      object: props.ticket?.object,
      content: props.ticket?.content
    });
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data) => {
    if (props.ticket.id) {
      data.id = props.ticket.id;
    }
    setDisableSubmit(true);
    // Unselected can only reach here if the required rule is bypassed; fall
    // back to the sentinel so the backend answers a field error rather than
    // this crashing on `undefined.value`.
    data.topic_id = data.topic_id?.value ?? OTHER_TOPIC_VALUE;
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
