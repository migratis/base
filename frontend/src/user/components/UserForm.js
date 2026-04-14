import { useState } from "react";
import { FormProvider, Controller, useForm } from 'react-hook-form';
import ReactFlagsSelect from 'react-flags-select';
import UserService from "../services/user.service";
import { useTranslation } from 'react-i18next';
import { PasswordValidation } from "./PasswordValidation";
import { toast } from 'react-toastify';
import InputField from '../../common/fields/InputField';
import ChoiceField from '../../common/fields/ChoiceField';
import TextareaField from '../../common/fields/TextareaField';
import DateField from '../../common/fields/DateField';
import { useNavigate } from "react-router-dom";
import { LinkToCguv } from "./LinkToCguv";

export const UserForm = (props) => {

	const { t } = useTranslation('userform');
	const [ country, setCountry ] = useState(props.profile ? props.profile.country_code : props.invitation.country_code);
	const [ passwordErrors, setPasswordErrors ] = useState('');  
	const [ serverErrors, setServerErrors ] = useState([]);    
	const [ disableSubmit, setDisableSubmit ] = useState(false);    
	const [ professional, setProfessional ] = useState(props.profile ? (props.profile.professional ? true : false) : (props.invitation.professional ? true : false));
	const [ cgu, setCgu ] = useState(false);
	const [ password, setPassword ] = useState('');
	const [ confPassword, setConfPassword ] = useState('');  
	const [ passwordOk, setPasswordOk ] = useState(false);
	const navigate = useNavigate();
	const methods = useForm({
		defaultValues: {
      		first_name: props.profile ? props.profile.first_name : props.invitation.first_name,
      		last_name: props.profile ? props.profile.last_name : props.invitation.last_name,
      		birthdate: props.profile ? new Date(props.profile.birthdate) : new Date(props.invitation.birthdate),
      		address: props.profile ? props.profile.address : props.invitation.address,
      		zipcode: props.profile ? props.profile.zipcode : props.invitation.zipcode,
      		city: props.profile ? props.profile.city : props.invitation.city,      
      		country: props.profile ? props.profile.country_code : props.invitation.country_code,   
      		professional: props.profile ? props.profile.professional : props.invitation.professional,                               
      		company: props.profile ? props.profile.company : props.invitation.company,
      		taxnumber: props.profile ? props.profile.taxnumber : props.invitation.taxnumber				  
    	}
  	});
	const { control, formState: {errors }, handleSubmit } = methods
    
  const emailPattern = {
    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
    message: t('email-invalid')
  }

	const onSubmit = async (data) => {
	  setDisableSubmit(true);
    if (props.profile && !props.register) {
      var language = localStorage.getItem('i18nextLng');
	    if (language.length > 2) {
	      language = language.slice(0, 2);
	    }
	    data.language = language;
      data.subscription = props.subscription;
      UserService.updateProfile(data).then((response) => { 
        if (response.detail[0].success) {
            props.setRefresh(!props.refresh);
			      toast.success(t(response.detail[0].success[0]));			
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
        setDisableSubmit(false);
      });
    } else {
      if (!passwordOk) {
        setPasswordErrors(true);
        setDisableSubmit(false);
      } else {
        if (props.invitation) {
          data.uidb64 = props.uidb64;
          data.token = props.token;
        }
        let language = localStorage.getItem('i18nextLng');
        data.language = language.slice(0, 2);
        UserService.register(data).then((response) => {
          if (response.detail[0].success) {
            if (props.invitation) {
              toast.success(t(response.detail[0].success[0]));
              navigate("/share/?id=" + props.id);
            } else {
              toast.success(t(response.detail[0].success[0]), {autoClose:false});
              navigate("/message", { state: t(response.detail[0].success[0])});
            }
          } else {
            if (response.detail[0] && response.detail[0].loc) {
              var message = {};
              for (var i=0;i<response.detail.length;i++) {            
                message[response.detail[i].loc[1]] = t(response.detail[i].msg);                
              }
              setServerErrors(message);
            }
            setDisableSubmit(false);
            toast.error(t('error-occured'));
          }
        });
      }
    }
  };

	return (
		<>
			<p className="text-center">
				{ t('fields-mandatory') }
				<span style={{color: 'red'}}>&nbsp;*</span>
			</p>
			<FormProvider {...methods}>
			  <form onSubmit={ handleSubmit(onSubmit) }>
				  <fieldset className="migratis-fieldset text-left">
					  { props.profile && !props.register ?
						  <div className="migratis-field">
							  <label htmlFor="email">
								  { t('email') }
							  </label>
							  <input type="text" className="form-control" disabled value={ props.profile.email }/>
							  <small className="form-text text-muted">
  								{ t('ask-to-change-email') }                                      
							  </small>
							  <br/>
							  <small className="form-text text-danger">
            			{ serverErrors?.email && serverErrors.email }                                 
        			  </small>
						  </div>
					  :
	            <>

	  						<InputField
								  name="email"
								  label={ t('email') }
								  required={true}  
								  maxLength={255} 
                  pattern={emailPattern}                             
								  serverError={serverErrors.email}
							  />
            
					      <InputField
						      name="password"
						      type="password"
						      label={ t('password') }
						      required={true}  
                  maxLength={50}                                      
						      dispatch={setPassword}
						      serverError={serverErrors.password??passwordErrors}
					      />
            
					      <InputField
						      name="confPassword"
						      type="password"
						      label={ t('confirm-password') }
						      required={true}    
                  maxLength={50}                                       
						      dispatch={setConfPassword}           
						      error={errors.confPassword??serverErrors.confPassword??passwordErrors}              
					      />

  						  <PasswordValidation
							    password={password}
							    confPassword={confPassword}
							    setPasswordOk={setPasswordOk}
							  />

	            </>  
	          }
              
					  <InputField
					    name="first_name"
					    label={ t('first_name') }
					    required={true}                    
              maxLength={50}                  
					    serverError={serverErrors.first_name}
					  />
	        
					  <InputField
					    name="last_name"
					    label={ t('last_name') }
					    required={true}                    
              maxLength={50}               
					    serverError={serverErrors.last_name}
					  />               

					  <div className={"migratis-field"}>
					    <label htmlFor="country" className={ errors.country || serverErrors.country ? 'text-danger' : '' }>
					      { t('country') }
					      <span style={{ color: 'red' }}>&nbsp;*</span>
					    </label>
					    <Controller 
					      name="country"
					      control={control}
					      rules={{ required: true }}
					      render={ ({ field: { onChange, value } }) => (
					        <ReactFlagsSelect
					          selectButtonClassName={ `bg-white menu-flags-button ${ errors.country || serverErrors.country ? 'onError' : '' }` }
					          selected={ country }
					          onSelect={ code => {
					            onChange(code);
					            setCountry(code);
					          }}
					          value={ value }
					          placeholder= { t('select-country') }
					        />
					      )}
					    />
					    <small className="form-text text-danger">
					      { !errors.country && serverErrors.country }    
					      { errors.country?.type === 'required' && t('select-country') }
					    </small>
					  </div>
					
						<DateField    
            	name="birthdate"    
              required={false}          
					  	dateFormat="dd-MM-yyyy"
					  	showMonthDropdown="true"
					  	showYearDropdown="true"
					  	dropdownMode="select"
              serverError={serverErrors.birthdate}
					  />
						<ChoiceField
							name="professional"
							option="true"  
              required={false}              
							label={ t('professional') }
							type="checkbox"                                     
							serverError={serverErrors.professional}     
							dispatch={setProfessional}           
					  />		  
            
	  				<InputField
						  name="company"
						  label={ t('company-name') }
						  required={professional?true:false}
              maxLength={150}             
						  serverError={serverErrors.company}
						  isVisible={professional?true:false}
					  />
	            
	  				<InputField
						  name="taxnumber"
						  label={ t('taxnumber') }
						  required={false}
              maxLength={30}             
						  serverError={serverErrors.taxnumber}
						  isVisible={professional?true:false}
					  />
          
					  <TextareaField
						  name="address"
						  label={ t('address') }
						  required={professional?true:false}               
              maxLength={200} 
						  rows={2}             
						  serverError={serverErrors.address}
						  isVisible={professional?true:false}                  
					  />
	              
	  				<InputField
						  name="zipcode"
						  label={ t('zipcode') }
						  required={professional?true:false}                    
              maxLength={20}               
						  serverError={serverErrors.zipcode}
						  isVisible={professional?true:false}                  
					  />

          
	  				<InputField
						  name="city"
						  label={ t('city') }
						  required={professional?true:false}                    
              maxLength={150}              
						  serverError={serverErrors.city}
						  isVisible={professional?true:false}                  
					  />

	          { ((props.profile && props.register) || props.invitation) &&
	  			    
              <ChoiceField
	              name="cgu"
	              option="true"
	              required={true}                
	              label={ t('accept-cgu') }                              
	              serverError={serverErrors.cgu}      
	              value={cgu}
	              dispatch={setCgu}
	              help={ <LinkToCguv/> }
	            />  
	          }

				    <div className="migratis-field text-center">
						  <button type="submit" disabled={disableSubmit} className="btn btn-primary btn-block">
                {props.profile && !props.register? t('modify') : t('validate')}
              </button>
				    </div> 
				  </fieldset>           
		    </form>
      </FormProvider>
		</>
	);  
};