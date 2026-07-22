import { useState, useEffect } from "react";
import { useLocation, Outlet } from "react-router-dom";
import { MenuLeft } from "./MenuLeft";
import { ToastContainer } from 'react-toastify';
import { SPCookieConsent } from "./CookieConsent";
import { BlockedModal } from "../modals/BlockedModal";
import { useTranslation } from "react-i18next";
import { IoMenuOutline as MenuIcon } from 'react-icons/io5';
import { useShell } from '../shell/ShellContext';

export const Layout = (props) => {
  const { t } = useTranslation('layout');
  const { useAuth, LoginComponent, userService } = useShell();
  const { user, setUser } = useAuth();
  const location = useLocation();
  const [ assistant, setAssistant ] = useState(false);
  const [ sessionExpiredShow, setSessionExpiredShow ] = useState(false);
  const [ mobileSidebarOpen, setMobileSidebarOpen ] = useState(false);

  useEffect(() => {
    if (localStorage.getItem("open-assistant")) {
      setAssistant(true);
      localStorage.removeItem("open-assistant");
    }
  }, []);

  // Refresh user profile from server on mount so fields added after login
  // (e.g. is_staff) are always up to date in localStorage and React state.
  useEffect(() => {
    if (user) {
      userService.getProfile().then((fresh) => {
        if (fresh && fresh.id) {
          localStorage.setItem("user", JSON.stringify(fresh));
          setUser(fresh);
        }
      }).catch(() => {});
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const handleSessionExpired = () => {
      const storedUser = localStorage.getItem("user");
      if (!storedUser || storedUser === 'false') {
        setSessionExpiredShow(true);
      }
    };

    window.addEventListener('session-expired', handleSessionExpired);

    if (localStorage.getItem("session_expired") === "true") {
      const storedUser = localStorage.getItem("user");
      if (!storedUser || storedUser === 'false') {
        setSessionExpiredShow(true);
      }
    }

    return () => {
      window.removeEventListener('session-expired', handleSessionExpired);
    };
  }, []);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setMobileSidebarOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleMobileSidebar = () => {
    setMobileSidebarOpen(!mobileSidebarOpen);
  };

  const closeMobileSidebar = () => {
    setMobileSidebarOpen(false);
  };

  return (
    <>
      <ToastContainer autoClose={2000} />
      
      <button className="mobile-menu-toggle" onClick={toggleMobileSidebar} aria-label="Toggle menu">
        <MenuIcon />
      </button>

      <MenuLeft 
        user={user}
        setUser={setUser}
        mobileOpen={mobileSidebarOpen}
        onMobileClose={closeMobileSidebar}
      />
      <div className="main-content">
        <Outlet context={{assistant, setAssistant, user, setUser}} />
      </div>
      { location.pathname !== "/cookies" &&
        <SPCookieConsent/>
      }
      <BlockedModal
        show={sessionExpiredShow}
        onHide={() => setSessionExpiredShow(false)}
        title={t('session-expired')}
        showCloseButton={false}
      >
        <LoginComponent
          setUser={setUser}
          setLoginModalShow={setSessionExpiredShow}
        />
      </BlockedModal>
    </>
  );
};
