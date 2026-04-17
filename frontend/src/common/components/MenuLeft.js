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
  IoDownloadOutline as DownloadOutline,
} from 'react-icons/io5';
import LangSelector from './LangSelector';
import UserService from "../../user/services/user.service";
import { toast } from 'react-toastify';
import Login from "../../user/components/Login";
import { BlockedModal as LoginModal } from "../modals/BlockedModal";
import { USER, INSTALLER } from '../../settings';
import logo from '../../img/logo.png';
import { moduleMenuItems } from '../../module_registry';

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
          <img src={logo} alt="logo" className="sidebar-logo" />
          <span className="sidebar-header-title">Base</span>
        </div>

        <div className="sidebar-content">

          {/* ── Installer (always visible, no auth required) ──────────────── */}
          { INSTALLER && (
            <div className="sidebar-section">
              <NavLink
                to="/installer"
                className={({isActive}) => `sidebar-item ${isActive ? 'active' : ''}`}
                onClick={props.onMobileClose}
              >
                <DownloadOutline />
                <span className="sidebar-label">Installer</span>
              </NavLink>
            </div>
          )}

          {moduleMenuItems.map(({ label, path }) => (
            <NavLink key={path} to={path} className={({isActive}) => `sidebar-item ${isActive ? 'active' : ''}`} onClick={props.onMobileClose}>
              <span className="sidebar-label">{label}</span>
            </NavLink>
          ))}

          {/* ── Auth-gated sections — activated when USER=true ────────────── */}
          { USER && props.user ? (
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

                <a href="/contact" className="sidebar-item" onClick={props.onMobileClose}>
                  <HelpOutline />
                  <span className="sidebar-label">{t('contact')}</span>
                </a>

                <div className="sidebar-item" onClick={() => { logOut(); props.onMobileClose(); }}>
                  <LogOutOutline />
                  <span className="sidebar-label">{t('logout')}</span>
                </div>
              </div>
            </>
          ) : USER && (
            <>
              <div className="sidebar-divider" />

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
            </>
          )}

        </div>
      </div>

      { USER &&
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
      }
    </>
  );
};