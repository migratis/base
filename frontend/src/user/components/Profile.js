import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import UserService from '../services/user.service'
import { toast } from 'react-toastify';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { Subscription } from '../../subscription/components/Subscription';
import { UserForm } from './UserForm';
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
          <header className="sticky-top">
            <div className="row">
              <div className="col-sm-12">
                <h2>{t('profile')}</h2>
              </div>
            </div>
          </header>      
          <Row>
            { SUBSCRIPTION &&
              <>
                <Col sm={12} lg={5} className="text-center">
                  <Subscription subscription={subscription} setSubscription={setSubscription}/> 
                </Col>  
                <Col className="separator" sm={12} lg={1}></Col>            
              </>
            }
            <Col sm={12} lg={SUBSCRIPTION?6:12}>          
              <h5 className="text-center">{t('your-informations')}</h5>
              <br/>
              <div className="text-center">             
                <button className="btn btn-danger"
                  onClick={() => handleConfirmDelete()}
                >
                  {t('delete-profile')}
                </button>
              </div>
              <br/>            
              <div className="text-center">             
                <button className="btn btn-secondary"
                  onClick={() => navigate("/password")}
                >
                  {t('password-change')}
                </button>
              </div>            
              <br/>
              <UserForm 
                profile={profile} 
                refresh={refresh} 
                setRefresh={setRefresh} 
                subscription={subscription}
              />
            </Col>
          </Row>
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
