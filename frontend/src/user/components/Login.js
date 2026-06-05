import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useForm } from 'react-hook-form';
import UserService from "../services/user.service";
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';

const Login = (props) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [serverErrors, setserverErrors] = useState([]);
  const { t } = useTranslation('login');
  const { register, formState: { errors }, handleSubmit, setValue } = useForm();
  const emailField = useRef(null);
  const passwordField = useRef(null);

  const [tfaMode, setTfaMode] = useState(false);
  const [tfaCode, setTfaCode] = useState("");
  const [tfaEmail, setTfaEmail] = useState("");
  const [rememberDevice, setRememberDevice] = useState(true);

  useEffect(() => {
    let interval = setInterval(() => {
      if (emailField.current && passwordField.current) {
        setValue("email", emailField.current.value);
        setValue("password", passwordField.current.value);
        clearInterval(interval)
      }
    }, 100);
  });

  // Shared success handler for both /login (trusted device) and /tfa/verify.
  const handleAuthSuccess = (response) => {
    toast.success(t("login-successfull"));
    localStorage.setItem("user", JSON.stringify(response.user));
    localStorage.removeItem("session_expired");
    props.setUser(response.user);
    if (props.setExpanded) props.setExpanded(false);
    if (location.pathname === "/home" || location.pathname === "/register") {
      var allowedStatuses = ["trialing", "infinite", "active"]
      if (allowedStatuses.indexOf(response.user.subscription) !== -1) {
        navigate("/account");
      } else {
        navigate("/subscribe");
      }
    } else {
      window.location.reload();
    }
    if (props.setLoginModalShow) props.setLoginModalShow(false);
  };

  const onSubmit = async (data) => {
    if (tfaMode) {
      UserService.tfaVerify({
        email: tfaEmail,
        code: tfaCode,
        remember_device: rememberDevice
      }).then(
        (response) => {
          if (response.user) {
            handleAuthSuccess(response);
          } else if (response.detail) {
            if (response.detail[0] && response.detail[0].loc) {
              var message = {};
              for (var i=0;i<response.detail.length;i++) {
                message[response.detail[i].loc[1]] = t(response.detail[i].msg);
              }
              setserverErrors(message);
              if (message.code) toast.error(message.code);
            } else {
              toast.error(t('error-occured'));
            }
          }
        }
      );
      return;
    }

    UserService.login({
      ...data,
      remember_device: rememberDevice
    }).then(
      (response) => {
        if (response.user) {
          handleAuthSuccess(response);
        } else if (response.tfa_required) {
          setTfaMode(true);
          setTfaEmail(response.email);
          setserverErrors([]);
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
                navigate("/contact", { state: t("account-not-activated")});
              } else {
                message[response.detail[i].loc[1]] = t(response.detail[i].msg);
              }
            }
            setserverErrors(message);
            if (error) toast.error(t('error-occured'));
          }
        }
      }
    );
  };

  const handleResendCode = () => {
    UserService.tfaResend(tfaEmail).then(
      (response) => {
        if (response.detail && response.detail[0] && response.detail[0].success) {
          toast.success(t("tfa-code-sent"));
        } else {
          toast.error(t('error-occured'));
        }
      }
    );
  };

  const handleBackToLogin = () => {
    setTfaMode(false);
    setTfaCode("");
    setserverErrors([]);
  };

  if (tfaMode) {
    return (
      <div>
        <p className="text-center">
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
                {...register("tfaCode", {
                  required: true,
                  minLength: 6,
                  maxLength: 6
                })}
                type="text"
                className={`form-control ${errors.tfaCode || serverErrors.code ? 'is-invalid' : ''}`}
                name="tfaCode"
                value={tfaCode}
                onChange={(e) => setTfaCode(e.target.value)}
                placeholder="000000"
                autoComplete="off"
              />
              <small className="form-text text-muted text-danger">
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

            <div className="migratis-field text-center">
              <br/><button className="btn btn-primary btn-block">{t('validate')}</button><br/>
            </div>
          </fieldset>
        </form>

        <div className="text-center">
          <button className="btn btn-link" onClick={handleResendCode}>
            {t('tfa-resend-code')}
          </button>
          <br/><br/>
          <button className="btn btn-secondary" onClick={handleBackToLogin}>
            {t('tfa-back')}
          </button>
        </div>
      </div>
    );
  }

  return (
      <div>
        <p className="text-center">
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
              <input { ...register("email", {
                required: true,
                maxLength: 150,
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: t('email-invalid')
                }}) }
                ref={emailField}
                type="text"
                className={ `form-control ${ errors.email || serverErrors.email ? 'is-invalid' : '' }` }
                name="email"
                value={ email }
                onChange={(e) => setEmail(e.target.value)}
              />
              <small className="form-text text-muted text-danger">
                { !errors.email && serverErrors.email }
                { errors.email?.type === 'required' && t("empty-field") }
                { errors.email && errors.email.type === "maxLength" && t("max-length-exceeded") }
              </small>
            </div>

            <div className="migratis-field">
              <label htmlFor="password" className={ errors.password || serverErrors.password ? 'text-danger' : '' }>
                { t('password') }
                <span style={{ color: 'red'} }>&nbsp;*</span>
              </label>
              <input { ...register("password", {
                required: true
                }) }
                ref={passwordField}
                type="password"
                className={ `form-control ${ errors.password || serverErrors.password ? 'is-invalid' : '' }` }
                name="password"
                value={ password }
                onChange={ (e) => setPassword(e.target.value) }
              />
              <small className="form-text text-muted text-danger">
                { !errors.password && serverErrors.password }
                { errors.password?.type === 'required' && t("empty-field") }
              </small>
            </div>

            <div className="migratis-field text-center">
              <br/><button className="btn btn-primary btn-block">{t('validate')}</button><br/>
            </div>
            </fieldset>
          </form>

          <div className="text-center">
              <Link to="/reset" onClick={() => props.setLoginModalShow(false)}>
                <br/><button className="btn btn-secondary btn-block">{ t('reset-password') }</button><br/>
              </Link>
              <br/>
              <Link className="nav-item btn btn-light" to="/register" onClick={() => props.setLoginModalShow(false)}>
                  {t('no-account-register')}
              </Link>
          </div>
        </div>
  );
};

export default Login;
