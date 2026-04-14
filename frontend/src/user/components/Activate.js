import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next';
import { useLocation, Link } from 'react-router-dom';
import UserService from "../services/user.service";

const Activate = () => {
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState('wait');   
  const [once, setOnce] = useState(false); 
  const { t } = useTranslation('activate');
  const search = useLocation().search;
  const uidb64 = new URLSearchParams(search).get('uidb64');
  const token = new URLSearchParams(search).get('token');

  const handleGoToLogin = () => {
    window.location.href = "/home/?login=1";
  };

  useEffect(() => {
    const doActivate = async () => {
      UserService.activate(uidb64, token).then( 
        (response) => {
          if (response.detail[0].success) {
            setMessage(response.detail[0].success[0]);
            setSuccess('ok');                        
          } else {
            if (response.detail[0] && response.detail[0].loc) {
              var message = {};
              for (var i=0;i<response.detail.length;i++) {            
                message[response.detail[i].loc[1]] = response.detail[i].msg;                
              }
            }
            setMessage(message);
            setSuccess('ko');                      
          }
        },
      );
    }
        
    if (!once) {
      setOnce(true);
      doActivate();
    }
        
  }, [once, uidb64, token]);

  return (
    <>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>{ t('email-activation') }</h2>
          </div>
        </div>
      </header>    
      <p className="text-center">
        { success === 'ok' ?
          <>
            <strong>{ t(message) }</strong>
            <br /><br />              
            <Link onClick={handleGoToLogin}>
              <button className="btn btn-primary btn-block">{ t('login') }</button>                        
            </Link>
          </>
        :
          <>
            { (message instanceof Object) ?
              <>
                <strong>{ t(message.user) }</strong>
                <br /><br />             
                <Link to="/register">
                  <button className="btn btn-primary btn-block">{ t('register') }</button>
                </Link>
              </>
            :
              <>
                { message.hasOwnProperty('token') ?
                  <>
                    <strong>{ t(message.token) }</strong>
                    <br /><br /> 
                    <Link to="/reset">
                      <button className="btn btn-primary btn-block">{ t('reset') }</button>
                    </Link>                  
                  </>
                :
                  <>
                    { message.hasOwnProperty('active') &&
                      <>
                        <strong>{ t(message.active) }</strong>
                        <br /><br />     
                        <Link onClick={handleGoToLogin}>
                          <button className="btn btn-primary btn-block">{ t('login') }</button>
                        </Link>                        
                      </>
                    }
                  </>
                }
              </>
            }
          </>
        }
        { success === 'ko' &&
          <>
            <strong>{ t('error-occured') }</strong>
            <br /><br />    
            { t('try-again-later') }                      
          </>
        }
      </p>
    </>
  );
} 

export default Activate