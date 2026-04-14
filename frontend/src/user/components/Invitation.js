import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import UserService from '../services/user.service'
import { toast } from 'react-toastify';
import { useNavigate } from "react-router-dom";
import { LoaderIndicator } from '../../common/components/LoaderIndicator';
import { useLocation } from 'react-router-dom';
import { UserForm } from './UserForm';

const Invitation = () => {
  const { t } = useTranslation('invitation');
  const navigate = useNavigate();
  const [ invitation, setInvitation ] = useState(null);
  const [ wait, setWait ] = useState(true);
  const search = useLocation().search;
  const id = new URLSearchParams(search).get('id');
  const uidb64 = new URLSearchParams(search).get('uidb64');
  const token = new URLSearchParams(search).get('token');

  useEffect(() => {  
    setWait(true); 
    UserService.getProfileWithToken(uidb64, token).then(
      (response) => {
        if (!response.detail) {
          setInvitation(response);
          setWait(false);
        } else {
          toast.error(t(response.detail[0].msg), {autoClose: false});
          navigate('/home');
        }
      }  
    );
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <LoaderIndicator/> 
      { !wait &&
      <>
      <header className="sticky-top">
        <div className="row">
            <div className="col-sm-12">
              <h2>{t('complete-invitation')}</h2>
            </div>
          </div>
        </header>      
        <UserForm 
          invitation={invitation} 
          uidb64={uidb64} 
          token={token} 
          id={id}
        />
      </>
      }

    </>
  );
}; 

export default Invitation;
