import { useEffect } from 'react'
import { lazyWithRetry } from "./common/tools/lazyWithRetry";
import { Routes, Route, useLocation } from "react-router-dom";
import "./App.scss";
import 'react-toastify/dist/ReactToastify.css';
import { Layout as Public, Layout as Private } from './common/components/Layout';
import { SUPPORT, SUBSCRIPTION, USER, COOKIE, CONTACT } from './settings';
import { moduleRoutes } from './module_registry';

const Home = lazyWithRetry(() => import('./common/components/Home'));
const Message = lazyWithRetry(() => import('./common/components/Message'));
const Cookies = lazyWithRetry(() => import('./common/components/Cookies'));
const Register = lazyWithRetry(() => import('./user/components/Register'));
const Invitation = lazyWithRetry(() => import('./user/components/Invitation'));
const Reset = lazyWithRetry(() => import('./user/components/Reset'));
const Password = lazyWithRetry(() => import('./user/components/Password'));
const Profile = lazyWithRetry(() => import('./user/components/Profile'));
const Subscribe = lazyWithRetry(() => import('./subscription/components/Subscribe'));
const Contact = lazyWithRetry(() => import('./support/components/Contact'));
const Tickets = lazyWithRetry(() => import('./support/components/Tickets'));
const Disclaimer = lazyWithRetry(() => import('./common/components/Disclaimer'));
const LegalNotice = lazyWithRetry(() => import('./common/components/LegalNotice'));
const RefundPolicy = lazyWithRetry(() => import('./common/components/RefundPolicy'));
const Licensing = lazyWithRetry(() => import('./common/components/Licensing'));
const Security = lazyWithRetry(() => import('./common/components/Security'));
const Status = lazyWithRetry(() => import('./common/components/Status'));
const Help = lazyWithRetry(() => import('./common/components/Help'));
const InstallerPage = lazyWithRetry(() => import('./installer/components/InstallerPage'));


const App = () => {

  const location = useLocation();
  useEffect(() => {

    if (window.location.hostname.includes("dev.")) {
      const meta = document.createElement("meta");
      meta.name = "robots";
      meta.content = "noindex";
      document.head.appendChild(meta);
    }

    window.scrollTo({
      top: 0,
      left: 0,
      behaviour: "smooth"
    });

  }, [location.pathname]);

  return (
    <>
      <Routes>
        <Route element={<Public private={false}/>}>
          <Route exact path="/home" element={<Home />} />
          <Route exact path="/Message" element={<Message />} />
          { COOKIE &&
            <>
              <Route exact path="/Cookies" element={<Cookies />} />
            </>
          }
          { USER &&
            <>
              <Route exact path="/register" element={<Register />} />
              <Route exact path="/invitation" element={<Invitation />} />
              <Route exact path="/reset" element={<Reset />} />
              <Route exact path="/password" element={<Password />} />
            </>
          }
          { (CONTACT || SUPPORT) &&
            <>
              <Route exact path="/contact" element={<Contact />} />
            </>
          }
          {/* Legal & information pages — all public, all linked from the footer.
              Their prose lives in the `legal` / `info` translation namespaces,
              so a deployment fills in its own identity without touching these. */}
          <Route exact path="/disclaimer" element={<Disclaimer />} />
          <Route exact path="/legal-notice" element={<LegalNotice />} />
          <Route exact path="/refund-policy" element={<RefundPolicy />} />
          <Route exact path="/security" element={<Security />} />
          <Route exact path="/status" element={<Status />} />
          <Route exact path="/help" element={<Help />} />
          <Route exact path='/installer' element={<InstallerPage/>} />
          {moduleRoutes.map(({ path, Component }) => (
            <Route key={path} path={path} element={<Component />} />
          ))}
          <Route path={"/"} element={<Home />} />
        </Route>
        <Route element={<Private private={true}/>}>
          { USER &&
            <>
              <Route exact path='/profile' element={<Profile/>} />
            </>
          }
          { SUPPORT &&
            <>
              <Route exact path="/support/ticket" element={<Tickets />} />
            </>
          }
          { SUBSCRIPTION &&
            <>
              <Route exact path='/subscribe' element={<Subscribe/>} />
            </>
          }
        </Route>
      </Routes>
    </>
  );
};

export default App;
