import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useForm } from 'react-hook-form';
import UserService from "../services/user.service";
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { firstEnabled } from '../../common/shell/collect';
import { landingRoutes } from '../../common/shell/registry';

const Login = (props) => {
  const navigate = useNavigate();
  const location = useLocation();
  // The user module authenticates; it does not decide what the app is *for*.
  // Whichever module ships the main workspace claims the landing page through
  // its shell.js `landingRoutes`; /home when no module contributes one.
  const landingPath = firstEnabled(landingRoutes)?.path || '/home';
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [serverErrors, setserverErrors] = useState([]);    
  const { t } = useTranslation('login');
  const { register, unregister, formState: { errors }, handleSubmit, setValue } = useForm({ mode: 'onChange' });
  const emailField = useRef(null);
  const passwordField = useRef(null);

  const [tfaMode, setTfaMode] = useState(false);
  const [tfaCode, setTfaCode] = useState("");
  const [tfaEmail, setTfaEmail] = useState("");
  const [rememberDevice, setRememberDevice] = useState(true);

  // Each input keeps its own `value` / `onChange` / `ref`, so react-hook-form's
  // must be composed with them rather than overwritten — otherwise the form
  // validates an empty store and answers "empty-field" for everything.
  const bind = (registration, localRef, dispatch) => ({
    ...registration,
    ref: (element) => {
      registration.ref(element);
      if (localRef) localRef.current = element;
    },
    onChange: (event) => {
      registration.onChange(event);
      dispatch(event.target.value);
    },
  });

  const emailRegistration = register("email", {
    required: true,
    maxLength: 150,
    pattern: {
      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
      message: t('email-invalid')
    }
  });
  const passwordRegistration = register("password", { required: true });
  // Only while the code step is on screen: a registered-but-absent required
  // field fails validation with nowhere to show the message, which would block
  // the ordinary login silently.
  const tfaCodeRegistration = tfaMode
    ? register("tfaCode", { required: true, minLength: 6, maxLength: 6 })
    : null;

  // A password manager can fill the inputs without firing a change event React
  // sees, which would leave the form thinking they are still empty. Poll the
  // DOM briefly after mount to pick such a fill up; a real keystroke goes
  // through `bind` above and needs none of this.
  useEffect(() => {
    const deadline = Date.now() + 5000;
    const interval = setInterval(() => {
      const filledEmail = emailField.current?.value;
      const filledPassword = passwordField.current?.value;
      if (filledEmail) {
        setEmail(filledEmail);
        setValue("email", filledEmail, { shouldValidate: true });
      }
      if (filledPassword) {
        setPassword(filledPassword);
        setValue("password", filledPassword, { shouldValidate: true });
      }
      if ((filledEmail && filledPassword) || Date.now() > deadline) {
        clearInterval(interval);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [setValue]);

  const onSubmit = async (data) => {
    if (tfaMode) {
      UserService.tfaVerify({
        email: tfaEmail,
        code: tfaCode,
        remember_device: rememberDevice
      }).then(
        (response) => {
          if (response.user) {          
            toast.success(t("login-successfull"));
            localStorage.setItem("user", JSON.stringify(response.user));
            localStorage.removeItem("session_expired");
            props.setUser(response.user);
            if (props.setExpanded) props.setExpanded(false);
            if (location.pathname === "/home" || location.pathname === "/register") {
              navigate(landingPath);
            } else {
              window.location.reload();
            }
            if (props.setLoginModalShow) props.setLoginModalShow(false);
          } else if (response.detail) {
            if (response.detail[0] && response.detail[0].loc) {
              var message = {};
              for (var i=0;i<response.detail.length;i++) {
                message[response.detail[i].loc[1]] = t(response.detail[i].msg);
              }            
              setserverErrors(message);
              if (message.code) toast.error(message.code);
            } else if (response.detail[0] && response.detail[0].error) {
              toast.error(t(response.detail[0].error[0]));
            } else {
              toast.error(t('error-occured'));
            }
          }
        }
      );
    } else {
      UserService.login({
        ...data,
        remember_device: rememberDevice
      }).then(
        (response) => {
          if (response.user) {          
            toast.success(t("login-successfull"));
            localStorage.setItem("user", JSON.stringify(response.user));
            localStorage.removeItem("session_expired");
            props.setUser(response.user);
            if (props.setExpanded) props.setExpanded(false);
            if (location.pathname === "/home" || location.pathname === "/register") {
              navigate(landingPath);
            } else {
              window.location.reload();
            }
            if (props.setLoginModalShow) props.setLoginModalShow(false);
          } else if (response.tfa_required) {
            setTfaMode(true);
            setTfaEmail(response.email);
          } else if (response.detail) {
            if (response.detail[0] && response.detail[0].loc) {
              var message = {};
              var error = true;
              for (var i=0;i<response.detail.length;i++) {
                if (response.detail[i].loc[1] === "email" && response.detail[i].msg === "account-not-activated") {
                  error = false;
                  toast.warning(t("confirm-link-in-email"), {autoClose:false});
                  props.setLoginModalShow(false);
                  navigate("/message", { state: t("confirm-link-in-email")});
                } else if (response.detail[i].loc[1] === "email" && response.detail[i].msg === "account-deleted") {
                  error = false;
                  toast.warning(t("account-deleted"), {autoClose:false});
                  props.setLoginModalShow(false);
                  navigate("/contact", { state: t("account-deleted")});
                } else {
                  message[response.detail[i].loc[1]] = t(response.detail[i].msg);
                }                        
              }            
              setserverErrors(message);
            }
            if (error) toast.error(t('error-occured'));
          }
        }
      );
    }
  };

  const handleResendCode = () => {
    UserService.tfaResend(tfaEmail).then(
      (response) => {
        if (response.detail && response.detail[0] && response.detail[0].success) {
          toast.success(t("tfa-code-sent"));
        } else if (response.detail) {
          if (response.detail[0] && response.detail[0].error) {
            toast.error(t(response.detail[0].error[0]));
          } else {
            toast.error(t('error-occured'));
          }
        }
      }
    );
  };

  const handleBackToLogin = () => {
    setTfaMode(false);
    setTfaCode("");
    setserverErrors([]);
    // Drop the code field, otherwise it keeps failing `required` behind a step
    // that is no longer displayed.
    unregister("tfaCode");
  };

  if (tfaMode) {
    return (
      <div>
        <p className="form-intro">
          {t('tfa-enter-code')}
        </p>
        <form onSubmit={handleSubmit(onSubmit)}>
          <fieldset className="migratis-fieldset">
            <div className="migratis-field">
              <label htmlFor="tfaCode" className={errors.tfaCode || serverErrors.code ? 'text-danger' : ''}>
                {t('tfa-code')}
                <span style={{ color: 'red' }}>&nbsp;*</span>
              </label>
              <input
                {...bind(tfaCodeRegistration, null, setTfaCode)}
                type="text"
                className={`form-control ${errors.tfaCode || serverErrors.code ? 'is-invalid' : ''}`}
                name="tfaCode"
                value={tfaCode}
                placeholder="000000"
                autoComplete="off"
              />
              <small className="form-text text-danger">
                {!errors.tfaCode && serverErrors.code}
                {errors.tfaCode?.type === 'required' && t("tfa-code-required")}
                {errors.tfaCode && (errors.tfaCode.type === "minLength" || errors.tfaCode.type === "maxLength") && t("tfa-code-invalid")}
              </small>  
            </div>

            <div className="migratis-field">
              <div className="form-check">
                <input
                  type="checkbox"
                  className="form-check-input"
                  id="rememberDevice"
                  checked={rememberDevice}
                  onChange={(e) => setRememberDevice(e.target.checked)}
                />
                <label className="form-check-label" htmlFor="rememberDevice">
                  {t('remember-device')}
                </label>
              </div>
            </div>

            <div className="form-actions">
              <button className="btn btn-primary">{t('validate')}</button>
            </div>
          </fieldset>
        </form>

        {/* Getting a new code and stepping back are escape hatches, not choices
            of equal weight with "Validate" — links, not a stack of buttons. */}
        <div className="form-alt-actions">
          <button type="button" className="btn btn-link" onClick={handleResendCode}>
            {t('tfa-resend-code')}
          </button>
          <button type="button" className="btn btn-link" onClick={handleBackToLogin}>
            {t('tfa-back')}
          </button>
        </div>
      </div>
    );
  }

  return (
      <div>
        <p className="form-intro">
            { t('fields-mandatory') }
            <span style={{ color: 'red' }}>&nbsp;*</span>
        </p>
          <form onSubmit={ handleSubmit(onSubmit) }>
            <fieldset className="migratis-fieldset">
            <div className="migratis-field">
              <label htmlFor="email" className={ errors.email || serverErrors.email ? 'text-danger' : '' }>
                { t('email') }
                <span style={{ color: 'red' }}>&nbsp;*</span>
              </label>
              <input { ...bind(emailRegistration, emailField, setEmail) }
                type="text"
                className={ `form-control ${ errors.email || serverErrors.email ? 'is-invalid' : '' }` }
                name="email"
                value={ email }
              />
              <small className="form-text text-danger">
                { !errors.email && serverErrors.email }
                { errors.email?.type === 'required' && t("empty-field") }
                { errors.email?.type === "maxLength" && t("max-length-exceeded") }
                { errors.email?.type === "pattern" && t("email-invalid") }
              </small>
            </div>

            <div className="migratis-field">
              <label htmlFor="password" className={ errors.password || serverErrors.password ? 'text-danger' : '' }>
                { t('password') }
                <span style={{ color: 'red'} }>&nbsp;*</span>
              </label>
              <input { ...bind(passwordRegistration, passwordField, setPassword) }
                type="password"
                className={ `form-control ${ errors.password || serverErrors.password ? 'is-invalid' : '' }` }
                name="password"
                value={ password }
              />
              <small className="form-text text-danger">
                { !errors.password && serverErrors.password }
                { errors.password?.type === 'required' && t("empty-field") }                                                                        
              </small>  
            </div>

            <div className="migratis-field">
              <div className="form-check">
                <input
                  type="checkbox"
                  className="form-check-input"
                  id="rememberDevice"
                  checked={rememberDevice}
                  onChange={(e) => setRememberDevice(e.target.checked)}
                />
                <label className="form-check-label" htmlFor="rememberDevice">
                  {t('remember-device')}
                </label>
              </div>
            </div>

            <div className="form-actions">
              <button className="btn btn-primary">{t('validate')}</button>
            </div>
            </fieldset>
          </form>

          {/* Signing in is the one action this form is for. Recovering a
              password and creating an account are ways out of it — they belong
              on one quiet line, not in a stack of three full-width buttons that
              makes the primary action indistinguishable. */}
          <div className="form-alt-actions">
              <Link to="/reset" onClick={() => props.setLoginModalShow(false)}>
                { t('reset-password') }
              </Link>
              <Link to="/register" onClick={() => props.setLoginModalShow(false)}>
                  {t('no-account-register')}
              </Link>
          </div>
        </div>
  );
};

export default Login;