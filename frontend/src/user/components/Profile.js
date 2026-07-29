import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import UserService from '../services/user.service'
import { toast } from 'react-toastify';
import { UserForm } from './UserForm';
import { Subscription } from '../../subscription/components/Subscription';
import { useNavigate } from "react-router-dom";
import { LoaderIndicator } from '../../common/components/LoaderIndicator';
import { CommonModal as ConfirmDeleteModal } from '../../common/modals/CommonModal';
import { useOutletContext } from "react-router-dom";
import { SUBSCRIPTION } from '../../settings';

const Profile = () => {
  const { t } = useTranslation('profile');// eslint-disable-next-line
  const { user, setUser } = useOutletContext();
  const [ profile, setProfile ] = useState(false);
  const navigate = useNavigate();
  const [ refresh, setRefresh ] = useState(false);   
  const [ subscription, setSubscription ] = useState(null);
  const [ confirmDeleteModalShow, setConfirmDeleteModalShow ] = useState(false);

  useEffect(() => {  
    if (user) {
      UserService.getProfile().then(
        (response) => {
          if (response.detail) {
            setProfile(false)
          } else {
            setProfile(response);
            setSubscription(response.subscription);
          }
        }
      );
    }
  }, [refresh]);// eslint-disable-line react-hooks/exhaustive-deps

  const handleConfirmDelete = () => {
    setConfirmDeleteModalShow(true);
  };
  
  const handleDelete = () => {
    UserService.deleteProfile().then(
      (response) => {
        if (response.detail[0].success) {
          toast.success(t(response.detail[0].success[0]));
          localStorage.setItem("user", null);
          setUser(null);
          navigate("/home");
        } else {
          if (response.detail[0] && response.detail[0].error[0]) {
            toast.error(t(response.detail[0].error[0]));
          }          
        }      
      }
    );
    setConfirmDeleteModalShow(false);
  };

  return (
    <>
      <LoaderIndicator/> 
      { user && profile &&
        <>
          {/* This renders inside the Account settings "Profile" tab, which
              already names the page — a second <h2>Profile</h2> here just said
              it twice. */}
          { SUBSCRIPTION &&
            <div className="mb-4">
              <Subscription subscription={subscription} setSubscription={setSubscription}/>
            </div>
          }
          <div className="page-panel-head">
            <h3 className="page-panel-title">{t('your-informations')}</h3>
            <div className="page-panel-actions">
              <button className="btn btn-sm btn-outline-secondary"
                onClick={() => navigate("/password")}
              >
                {t('password-change')}
              </button>
              <button className="btn btn-sm btn-outline-danger"
                onClick={() => handleConfirmDelete()}
              >
                {t('delete-profile')}
              </button>
            </div>
          </div>
          <UserForm
            profile={profile}
            refresh={refresh}
            setRefresh={setRefresh}
            subscription={subscription}
          />
        </>
      }
      <ConfirmDeleteModal
        show={confirmDeleteModalShow}
        onHide={() => setConfirmDeleteModalShow(false)}
        title={t('confirm-remove-profile')}        
      >
        <div className="text-center">
          {t('remove-profile-text')}
        </div>
        { subscription && subscription.access &&
          <div className="text-center">
            <br/>
            {t('remove-profile-subscription-text')}
          </div>
        }
        <div className="text-center">
          <br/>
          <button onClick={ () => handleDelete() } className="btn btn-danger btn-block btn-wide">
            {t('delete-profile')}
          </button>
          <br/><br/>
        </div>
      </ConfirmDeleteModal>       
    </>
  );
}; 

export default Profile;
