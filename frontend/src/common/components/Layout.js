import { useState, useEffect } from "react";
import { useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../../user/hooks/useAuth";
import { MenuLeft } from "./MenuLeft";
import { ToastContainer } from 'react-toastify';
import { SPCookieConsent } from "./CookieConsent";
import { BlockedModal } from "../modals/BlockedModal";
import Login from "../../user/components/Login";
import { useTranslation } from "react-i18next";
import { IoMenuOutline as MenuIcon } from 'react-icons/io5';
import { USER } from '../../settings';

export const Layout = (props) => {
  const { t } = useTranslation('layout');
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
      { USER &&
        <BlockedModal
          show={sessionExpiredShow}
          onHide={() => setSessionExpiredShow(false)}
          title={t('session-expired')}
          showCloseButton={false}
        >
          <Login
            setUser={setUser}
            setLoginModalShow={setSessionExpiredShow}
          />
        </BlockedModal>
      }
    </>
  );
};
