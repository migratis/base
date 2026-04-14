import { useState, useEffect } from "react";
import LangSelector from './LangSelector';
import logo from '../../img/logo.png';
import { useTranslation } from 'react-i18next';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import { 
  IoCardOutline as CardOutline, 
  IoPerson as Person,
  IoHelpBuoy as HelpBuoy,
  IoMailOutline as MailOutline
} from 'react-icons/io5';
import { MenuLeft } from "./MenuLeft";
import UserService from "../../user/services/user.service";
import { toast } from 'react-toastify';
import Login from "../../user/components/Login";
import { BlockedModal as LoginModal } from "../modals/BlockedModal";
import { useQuery } from '../hooks/useQuery';
import { useNavigate } from "react-router-dom";
import { SUPPORT, SUBSCRIPTION, GENERATOR } from "../../settings";
import AIUsageIndicator from '../../generator/components/AIUsageIndicator';

export const Header = (props) => {
  const { t } = useTranslation('layout');
  const query = useQuery();
  const [ loginModalShow, setLoginModalShow ] = useState(false);
  const [ expanded, setExpanded ] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!props.user) {
      if (query.get('login') || props.private) handleLogin();
    } else {
      window.addEventListener("disconnected", handleLogin);
    }
  }, [props.user, query, props.private]);// eslint-disable-line react-hooks/exhaustive-deps

  const logOut = () => {
    window.removeEventListener("disconnected", handleLogin);
    UserService.logout().then(
      (response) => {
        if (response.detail[0].success) {
          toast.success(t(response.detail[0].success));
        } else {
          toast.error(t(response.detail[0].error));
        }
      }
    );
    setExpanded(false);
    navigate("/home");
    props.setUser(false);
    localStorage.removeItem("user");
  };

  const handleLogin = () => {
    setLoginModalShow(true);
  };

	return (
    <>
      <div className="menu-top">
        <Navbar 
          expanded={expanded}
          onToggle={() => setExpanded(!expanded)}
          onSelect={() => setExpanded(false)}
          expand="lg">
          <div className="nav-stuff">
            <Navbar.Brand href="/">
              <img alt="Migratis" className='logo' src={logo} />
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="default-navbar-nav" />          
            <div className="nav-stuff-items"> 
              <Navbar.Collapse id="default-navbar-nav">
                <Nav>
                  <Nav.Link className="nav-item btn btn-light" href={(props.user && SUPPORT) ? "/support/ticket" : "/contact"}>
                    {(props.user && SUPPORT) ? 
                      <>
                        {t('support')}&nbsp;
                        <span className="link">
                          <HelpBuoy color={'#000000'} title={t('support')}/>
                        </span>
                      </>                        
                    : 
                      <>
                        {t('contact')}&nbsp;
                        <span className="link">
                          <MailOutline color={'#000000'} title={t('contact')}/>
                        </span>
                      </>
                    }
                  </Nav.Link>   
               
                </Nav>
                <Nav className="ms-auto">
                { props.user ? 
                  <>
                    { (!props.user.subscription) && SUBSCRIPTION &&
                      <Nav.Link className="nav-item btn btn-light" href="/subscribe">
                        {t('subscribe')}
                        &nbsp;<CardOutline color={'#000000'} title={t('subscribe')} height="25px" width="25px"/>
                      </Nav.Link>
                    }
                    { GENERATOR &&
                      <AIUsageIndicator />
                    }   
                    <Nav.Link className="nav-item btn btn-light" href="/profile">
                      {t('profile')}
                      &nbsp;<Person color={'#000000'} title={t('profile')} height="25px" width="25px"/>
                    </Nav.Link>                           
                    <Nav.Link eventKey={1} className="nav-item btn btn-secondary" onClick={logOut}>
                      {t('logout')}
                    </Nav.Link>          
                  </>
                :
                  <>
                    <Nav.Link className="nav-item btn btn-light" href="/register">
                      {t('register')}
                    </Nav.Link>              
                    <Nav.Link eventKey={2} className="nav-item btn btn-secondary" onClick={handleLogin}>                
                      {t('login')}
                    </Nav.Link>                           
                  </>
                }
                </Nav>
              </Navbar.Collapse>
            </div>
          </div>
        </Navbar>
        <div className="message-zone">
          <div className="language-selector">
            <LangSelector/>
          </div>

        </div>        
      </div>
      <MenuLeft 
        user={props.user}
        opened={props.opened}
        setOpened={props.setOpened}
        expanded={expanded}
      />
      <LoginModal
        show={loginModalShow}
        onHide={() => setLoginModalShow(false)}
        title={t('login')}
      >
        <Login      
          setUser={props.setUser}
          setLoginModalShow={setLoginModalShow}
          setExpanded={setExpanded}
        />
      </LoginModal>
    </>
  );
}