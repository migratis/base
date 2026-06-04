import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  IoPersonOutline as PersonOutline,
  IoLogOutOutline as LogOutOutline,
  IoHelpBuoyOutline as HelpOutline,
  IoGlobeOutline as GlobeOutline,
} from 'react-icons/io5';
import LangSelector from './LangSelector';
import UserService from "../../user/services/user.service";
import { toast } from 'react-toastify';
import Login from "../../user/components/Login";
import { BlockedModal as LoginModal } from "../modals/BlockedModal";
import { SUPPORT } from '../../settings';
import logo from '../../img/logo.png';

export const MenuLeft = (props) => {
  const { t } = useTranslation('layout');
  const navigate = useNavigate();
  const [ expanded, setExpanded ] = useState(false);
  const [ loginModalShow, setLoginModalShow ] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setExpanded(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (props.mobileOpen) {
      setExpanded(true);
    }
  }, [props.mobileOpen]);

  const logOut = () => {
    UserService.logout().then(
      (response) => {
        if (response.detail[0].success) {
          toast.success(t(response.detail[0].success));
        } else {
          toast.error(t(response.detail[0].error));
        }
      }
    );
    navigate("/home");
    props.setUser(false);
    localStorage.removeItem("user");
  };

  const handleLogin = () => {
    setLoginModalShow(true);
  };

  return (
    <>
      <div className={`sidebar-container ${expanded ? 'expanded' : ''} ${props.mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <img src={logo} alt="Migratis" className="sidebar-logo" />
          <span className="sidebar-header-title">Migratis</span>
        </div>

        <div className="sidebar-content">
          {props.user ? (
            <>
<div className="sidebar-divider" />

              <div className="sidebar-section">
                <NavLink
                  to="/profile"
                  className={({isActive}) => `sidebar-item ${isActive ? 'active' : ''}`}
                  onClick={props.onMobileClose}
                >
                  <PersonOutline />
                  <span className="sidebar-label">{t('profile')}</span>
                </NavLink>
                
                <div className="sidebar-item">
                  <GlobeOutline />
                  <span className="sidebar-label">
                    <LangSelector />
                  </span>
                </div>
                
                {SUPPORT ? (
                  <a href="/support/ticket" className="sidebar-item" onClick={props.onMobileClose}>
                    <HelpOutline />
                    <span className="sidebar-label">{t('support')}</span>
                  </a>
                ) : (
                  <a href="/contact" className="sidebar-item" onClick={props.onMobileClose}>
                    <HelpOutline />
                    <span className="sidebar-label">{t('contact')}</span>
                  </a>
                )}

                <div className="sidebar-item" onClick={() => { logOut(); props.onMobileClose(); }}>
                  <LogOutOutline />
                  <span className="sidebar-label">{t('logout')}</span>
                </div>
              </div>
            </>
          ) : (
            <div className="sidebar-section">
              <div className="sidebar-item" onClick={() => { handleLogin(); props.onMobileClose(); }}>
                <PersonOutline />
                <span className="sidebar-label">{t('login')}</span>
              </div>
              
              <div className="sidebar-item">
                <GlobeOutline />
                <span className="sidebar-label">
                  <LangSelector />
                </span>
              </div>
              
              <a href="/contact" className="sidebar-item" onClick={props.onMobileClose}>
                <HelpOutline />
                <span className="sidebar-label">{t('contact')}</span>
              </a>
            </div>
          )}
        </div>
      </div>

      <LoginModal
        show={loginModalShow}
        onHide={() => setLoginModalShow(false)}
        title={t('login')}
      >
        <Login      
          setUser={props.setUser}
          setLoginModalShow={setLoginModalShow}
        />
      </LoginModal>
    </>
  );
};
