import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  IoPersonOutline as PersonOutline,
  IoLogOutOutline as LogOutOutline,
  IoHelpBuoyOutline as HelpOutline,
  IoAtOutline as AtOutline,
  IoAtCircleOutline as AtCircleOutline,
  IoGlobeOutline as GlobeOutline,
  IoChevronDown as ChevronDown,
  IoChevronUp as ChevronUp,
  IoGridOutline as GridOutline,
} from 'react-icons/io5';
import LangSelector from './LangSelector';
import UserService from "../../user/services/user.service";
import { toast } from 'react-toastify';
import CreditsIndicator from '../../credits/components/CreditsIndicator';
import Login from "../../user/components/Login";
import { BlockedModal as LoginModal } from "../modals/BlockedModal";
import { MIGRATIS, GENERATOR, CREDITS, SUPPORT } from '../../settings';
import { LeftMenu as GeneratorLeftMenu } from '../../generator/components/LeftMenu';
import logo from '../../img/logo.png';

export const MenuLeft = (props) => {
  const { t } = useTranslation('layout');
  const navigate = useNavigate();
  const [ expanded, setExpanded ] = useState(false);
  const [ loginModalShow, setLoginModalShow ] = useState(false);
  const [ openSections, setOpenSections ] = useState({
    migratis: true,
    generator: true,
  });

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setExpanded(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleSection = (section) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  useEffect(() => {
    if (props.mobileOpen) {
      setExpanded(true);
    }
  }, [props.mobileOpen]);

  // Open the login modal when any action needs an authenticated session but the
  // visitor is anonymous (e.g. clicking "pay" on the plans page). Mirrors the
  // Header's handling so the prompt works on pages that render only the sidebar.
  useEffect(() => {
    const handleDisconnected = () => setLoginModalShow(true);
    window.addEventListener("disconnected", handleDisconnected);
    return () => window.removeEventListener("disconnected", handleDisconnected);
  }, []);

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
              {(CREDITS || GENERATOR) && (
                <div className="sidebar-section">
                  {CREDITS && <CreditsIndicator compact />}
                  {GENERATOR && <GeneratorLeftMenu onMobileClose={props.onMobileClose} user={props.user} />}
                </div>
              )}

              {MIGRATIS && (
                <div className="sidebar-section">
                  <div
                    className="sidebar-section-header"
                    onClick={() => toggleSection('migratis')}
                  >
                    <GridOutline />
                    <span className="sidebar-section-title">{t('migratis')}</span>
                    <span className="sidebar-section-chevron">
                      {openSections.migratis ? <ChevronUp /> : <ChevronDown />}
                    </span>
                  </div>
                  {openSections.migratis && (
                    <>
                      <NavLink
                        to="/migratis/item"
                        className={({isActive}) => `sidebar-item ${isActive ? 'active' : ''}`}
                        onClick={props.onMobileClose}
                      >
                        <AtOutline />
                        <span className="sidebar-label">{t('items')}</span>
                      </NavLink>
                      <NavLink
                        to="/migratis/subitem"
                        className={({isActive}) => `sidebar-item ${isActive ? 'active' : ''}`}
                        onClick={props.onMobileClose}
                      >
                        <AtCircleOutline />
                        <span className="sidebar-label">{t('subitems')}</span>
                      </NavLink>
                    </>
                  )}
                </div>
              )}

<div className="sidebar-divider" />

              <div className="sidebar-section">
                <NavLink
                  to="/account"
                  className={({isActive}) => `sidebar-item ${isActive ? 'active' : ''}`}
                  onClick={props.onMobileClose}
                >
                  <PersonOutline />
                  <span className="sidebar-label">{t('account-settings')}</span>
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
