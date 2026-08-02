import { useState, useEffect, Suspense } from "react";
import { useLocation, Outlet } from "react-router-dom";
import { MenuLeft } from "./MenuLeft";
import { ToastContainer } from 'react-toastify';
import { SPCookieConsent } from "./CookieConsent";
import { Footer } from "./Footer";
import { LoaderIndicator } from "./LoaderIndicator";
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

  // An expired session is only worth interrupting for on a page that needed the
  // session. The flag lives in localStorage and used to survive until the next
  // successful login, so a single 401 walled the *public* site — home, the legal
  // pages, help — behind a modal a visitor entitled to browse anonymously could
  // not even close (`backdrop="static"`, no close button). Reading the flag now
  // consumes it, and only a private page turns it into a prompt.
  const isPrivate = props.private;

  useEffect(() => {
    const consumeSessionExpired = () => {
      const storedUser = localStorage.getItem("user");
      if (storedUser && storedUser !== 'false') return;

      localStorage.removeItem("session_expired");
      if (isPrivate) {
        setSessionExpiredShow(true);
      }
    };

    window.addEventListener('session-expired', consumeSessionExpired);

    if (localStorage.getItem("session_expired") === "true") {
      consumeSessionExpired();
    }

    return () => {
      window.removeEventListener('session-expired', consumeSessionExpired);
    };
  }, [isPrivate]);

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
      {/* The page gets a boundary of its own. Every route is lazy and every
          page pulls its own i18n namespace, so without one the suspension
          climbed to the root boundary in index.js and replaced the entire
          document — sidebar and footer included — with the spinner. Landing on
          a public page with a session open did that four or five times in a
          row (one per module namespace), which is what read as a blinking
          page. Held here, the shell stays put and only the content waits. */}
      <div className="main-content">
        <Suspense fallback={<LoaderIndicator always />}>
          <Outlet context={{assistant, setAssistant, user, setUser}} />
        </Suspense>
      </div>
      {/* The closing band, after the content and outside `.main-content` so it
          spans the full width beside the sidebar. It carries the legal and
          information links, which have to be reachable from every page. */}
      <Footer user={user} />
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
