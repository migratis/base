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
import { toast } from 'react-toastify';
import { BlockedModal as LoginModal } from "../modals/BlockedModal";
import { SUPPORT } from '../../settings';
import logo from '../../img/logo.png';
import { sidebarSlots } from '../shell/registry';
import { useShell } from '../shell/ShellContext';

export const MenuLeft = (props) => {
  const { t } = useTranslation('layout');
  const navigate = useNavigate();
  const { LoginComponent, userService } = useShell();
  const [ expanded, setExpanded ] = useState(false);
  const [ loginModalShow, setLoginModalShow ] = useState(false);

  // Module-contributed sidebar snippets, discovered from each module's
  // shell.js (see common/shell/registry.js). Inline widgets share one section;
  // `section: true` snippets (collapsible groups) get their own.
  const enabledSlots = sidebarSlots.filter((slot) => slot.enabled());
  const inlineSlots = enabledSlots.filter((slot) => !slot.section);
  const sectionSlots = enabledSlots.filter((slot) => slot.section);

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

  // Open the login modal when any action needs an authenticated session but the
  // visitor is anonymous (e.g. clicking "pay" on the plans page). Mirrors the
  // Header's handling so the prompt works on pages that render only the sidebar.
  useEffect(() => {
    const handleDisconnected = () => setLoginModalShow(true);
    window.addEventListener("disconnected", handleDisconnected);
    return () => window.removeEventListener("disconnected", handleDisconnected);
  }, []);

  const logOut = () => {
    userService.logout().then(
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
              {inlineSlots.length > 0 && (
                <div className="sidebar-section">
                  {inlineSlots.map((slot) => (
                    <slot.Component
                      key={slot.id}
                      user={props.user}
                      onMobileClose={props.onMobileClose}
                    />
                  ))}
                </div>
              )}

              {sectionSlots.map((slot) => (
                <div className="sidebar-section" key={slot.id}>
                  <slot.Component
                    user={props.user}
                    onMobileClose={props.onMobileClose}
                  />
                </div>
              ))}

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
        <LoginComponent
          setUser={props.setUser}
          setLoginModalShow={setLoginModalShow}
        />
      </LoginModal>
    </>
  );
};
