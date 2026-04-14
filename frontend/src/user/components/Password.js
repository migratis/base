import { useState } from 'react'
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate } from 'react-router-dom';
import { PasswordValidation } from "./PasswordValidation";
import UserService from "../services/user.service";
import { useTranslation } from 'react-i18next';
import { useAuth } from "../../user/hooks/useAuth";
import { toast } from 'react-toastify';

const Password = () => {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [ message, setMessage ] = useState(''); 
	const [ oldPassword, setOldPassword ] = useState(''); 
  const [ password, setPassword ] = useState('');
  const [ confPassword, setConfPassword ] = useState('');
  const [ passwordErrors, setPasswordErrors ] = useState('');
  const [ serverErrors, setserverErrors ] = useState([]);
  const search = useLocation().search;
  const uidb64 = new URLSearchParams(search).get('uidb64');
  const token = new URLSearchParams(search).get('token');    
  const { t } = useTranslation('password');
  const [ passwordOk, setPasswordOk ] = useState(false);
  const { register, formState: { errors }, handleSubmit } = useForm();

  const onSubmit = async (data) => {
    if (!passwordOk) {
      setPasswordErrors(true);
    } else {
      setPasswordErrors(false);
      UserService.password(user, uidb64, token, data).then(
        (response) => {
          if (response.detail[0].success) {
            toast.success(t(response.detail[0].success[0]));
            setUser(false);
            localStorage.setItem("user", null);
						navigate("/profile");
          } else {
            if (response.detail[0] && response.detail[0].loc) {
              var message = {};
              for (var i=0;i<response.detail.length;i++) {
                if (response.detail[i].loc[1] === 'error') {
                  setMessage(t(response.detail[i].msg));
                } else {
                  message[response.detail[i].loc[1]] = t(response.detail[i].msg);  
                }              
              }
              setserverErrors(message);
            }
            toast.error(t('error-occured'));                        
          }
	    }); 
    }
  };

  return (
    <>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>{ t('change-password') }</h2>
          </div>
        </div>
      </header>                
      <p className="text-center">
        {t('fields-mandatory')}
        <span style={{color: 'red'}}>&nbsp;*</span>
      </p>
      <form onSubmit={ handleSubmit(onSubmit) }>
        <fieldset className="migratis-fieldset text-left">
					{ !uidb64 && !token &&
						<div className="migratis-field">
            	<label htmlFor="oldPassword" className={ errors.oldPassword || serverErrors.oldPassword ? 'text-danger' : '' }>
                { t('old-password') }
                <span style={{ color: 'red'} }>&nbsp;*</span>
            	</label>
            	<input { ...register("oldPassword", { required: true }) }
	              type="password"
              	className={ `form-control ${ passwordErrors || errors.oldPassword || serverErrors.oldPassword ? 'is-invalid' : '' }` }
              	name="oldPassword"
              	value={ oldPassword }
              	onChange={ (e) => setOldPassword(e.target.value) }
            	/>
            	<small className="form-text text-danger">
	              { !errors.oldPassword && serverErrors.oldPassword }
              	{ errors.oldPassword?.type === 'required' && t("empty-field") }                                                                        
            	</small>  
						</div>
					}					
					<div className="migratis-field">
            <label htmlFor="password" className={ errors.password || serverErrors.password ? 'text-danger' : '' }>
                { t('password') }
                <span style={{ color: 'red'} }>&nbsp;*</span>
            </label>
            <input { ...register("password", { required: true }) }
              type="password"
              className={ `form-control ${ passwordErrors || errors.password || serverErrors.password ? 'is-invalid' : '' }` }
              name="password"
              value={ password }
              onChange={ (e) => setPassword(e.target.value) }
            />
            <small className="form-text text-danger">
              { !errors.password && serverErrors.password }
              { errors.password?.type === 'required' && t("empty-field") }                                                                        
            </small>  
					</div>
          <div className="migratis-field">
            <label htmlFor="confPassword" className={ errors.confPassword || serverErrors.confPassword ? 'text-danger' : '' }>
              { t('confirm-password') }
              <span style={{ color: 'red' }}>&nbsp;*</span>
            </label>
            <input { ...register("confPassword", { required: true })}
              type="password"
              className={ `form-control ${ passwordErrors || errors.confPassword || serverErrors.confPassword ? 'is-invalid' : '' }` }
              name="confPassword"
              value={ confPassword }
              onChange={ (e) => setConfPassword(e.target.value) }
            />
            <small className="form-text text-danger">
              { !errors.confPassword && serverErrors.confPassword }
              { errors.confPassword?.type === 'required' && t("empty-field") }                                                                        
            </small>
          </div>
					<PasswordValidation
						password={password}
						confPassword={confPassword}
						setPasswordOk={setPasswordOk}
					/>
          <div className='migratis-field texyt-center'>
              <button className="btn btn-primary btn-block">{t('validate')}</button>
          </div>	          
          { message && 
              <div >
                  <div 
                      className = {"alert alert-danger"}
                      role="alert">
                      {message}
                  </div>
              </div>
          }
				</fieldset>										                  
      </form>
    </>
  )
}
 
export default Password