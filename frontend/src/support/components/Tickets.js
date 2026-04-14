import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import SupportService from '../services/support.service';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { IoAddCircleOutline as AddCircleOutline } from 'react-icons/io5';
import { CommonModal as TicketModal } from '../../common/modals/CommonModal';
import TicketForm from './TicketForm';
import { UploadFile } from "./UploadFile";
import download from 'downloadjs';
import { Tabs, Tab } from 'react-bootstrap';
import Ticket from './Ticket';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';
import { toast } from 'react-toastify';
import { useQuery } from '../../common/hooks/useQuery';
import { COLOR_LINK } from "../../settings";

const Tickets = () => {
  const { t } = useTranslation('support');
  const [ tickets, setTickets ] = useState({});
  const [ openTickets, setOpenTickets ] = useState({});
  const [ closedTickets, setClosedTickets ] = useState({});  
  const [ refresh, setRefresh ] = useState(false);
  const [ ticket, setTicket ] = useState(null);
  const newTicket = {
    id: null,   
    topic: null,
    object: null, 
    content: null, 
  }
  const [ ticketModalShow, setTicketModalShow ] = useState(false);
  const [ wait, setWait ] = useState(false);
  const [ activeKey, setActiveKey ] = useState("0");
  const [ uploadModalShow, setUploadModalShow ] = useState(false);  
  const [ currentTab, setCurrentTab ] = useState(
    localStorage.getItem("ticket-tab") ?
    localStorage.getItem("ticket-tab") : 'open_tickets'
  );
  const query = useQuery();  

  useEffect(() => {
    if (query.get("id")) {
      setActiveKey(parseInt(query.get("id")));
      handleAccordion(parseInt(query.get("id")));
    }
  }, [query]);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setWait(true);
    SupportService.getFullTickets().then(
      (response) => {
        if (!response.stack && !response.detail) {
          setTickets(response);
          setOpenTickets(response.filter((item) => item.status !== 'c'));
          setClosedTickets(response.filter((item) => item.status === 'c'));
          setWait(false);
        }
      }
    );
  }, [refresh]);
  
  const handleSelectTab = (tab) => {
    localStorage.setItem("ticket-tab", tab);
    setCurrentTab(tab);
  };

  const handleAccordion = (id) => {
    var elem = document.getElementById("anchor-" + id);
    if (elem?.offsetTop > 0) {
      window.scrollTo({
        top: elem.offsetTop - 500,
        behavior: 'smooth',
      });
    }
  };

  const handleTicketEdit = (id=null) => {
    if (id) {
      setTicket(tickets.find((elem) => {
        return elem.id === id;
      }));
    } else {
      setTicket(newTicket);
    }
    setTicketModalShow(true);
  };

  const handleUpload = (id) => {
    setTicket(tickets.find((elem) => {
      return elem.id === id;
    }));
    setUploadModalShow(true); 
  };

  function handleDownload(file) {
    SupportService.download(file).then(
      (response) => {
        download(new Blob([response]), file.filename, file.mime);
      }
    );
  }

  const handleClose = (id) => {
    if (window.confirm(t('confirm-close-ticket'))) {
      SupportService.closeTicket(id).then(
        (response) => {
          if (response.detail[0].success) {
            toast.success(t(response.detail[0].success[0]));
            setRefresh(!refresh);
          } else {
            toast.error(t('error-occured'));
          }
        }
      );      
    }      
  };

  const closeAndUpdateTicketModal = (id) => {
    setTicketModalShow(false);
    setRefresh(!refresh);
    setActiveKey(id)
    handleAccordion(id);
  }

  const closeAndUpdateUploadModal = (id) => {
    setUploadModalShow(false);
    setRefresh(!refresh);
    setActiveKey(id)    
    handleAccordion(id);
  };
  
  return (
    <>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-6">
            <h2>{t('your-tickets')}</h2>
          </div>
          <div className="col-sm-6">
            <span className="link float-end" onClick={() => handleTicketEdit()}>
              <AddCircleOutline color={null} title={t('add-ticket')} />
            </span>            
          </div>          
        </div>
      </header>    
      <LoaderIndicator />     
      { !wait && (openTickets.length > 0 || closedTickets.length > 0) ?
        <Tabs 
          defaultActiveKey="open_tickets" 
          id="projection-tab"
          activeKey={currentTab}
          onSelect={(tab) => handleSelectTab(tab)}
          className="mb-3"
        >
          <Tab eventKey="open_tickets" title={t('open-tickets')} >
            <Container>
              { openTickets.length > 0 ? openTickets.map(
                item =>
                  <Ticket
                    key={item.id}
                    ticket={item}
                    handleUpload={handleUpload}
                    handleDownload={handleDownload}                    
                    handleTicketEdit={handleTicketEdit}
                    refresh={refresh}                    
                    setRefresh={setRefresh}
                    closeAndUpdateTicketModal={closeAndUpdateTicketModal}
                    closeAndUpdateUploadModal={closeAndUpdateUploadModal}
                    handleAccordion={handleAccordion}
                    activeKey={activeKey}                    
                    setActiveKey={setActiveKey}
                    handleClose={handleClose}                                                 
                  />              
                )
              :
                <Row className="stripped">
                  <Col className="col-head text-center" sm={12} lg={12}>
                    {t('no-opened-ticket-yet-create-one')}&nbsp;
                    <span className="link action" onClick={() => handleTicketEdit()}>
                      <AddCircleOutline color={COLOR_LINK} title={t('add-ticket')} />
                    </span>              
                  </Col>
                </Row>
              }
            </Container>
          </Tab>
          <Tab eventKey="closed_tickets" title={t('closed-tickets')} >
            { closedTickets.length > 0 && closedTickets.map(
              item =>
                <Ticket
                  key={item.id}
                  ticket={item}
                  handleUpload={handleUpload}
                  handleDownload={handleDownload}                    
                  handleTicketEdit={handleTicketEdit}
                  refresh={refresh}
                  setRefresh={setRefresh}
                  closeAndUpdateTicketModal={closeAndUpdateTicketModal}                  
                  closeAndUpdateUploadModal={closeAndUpdateUploadModal}
                  handleAccordion={handleAccordion}
                  activeKey={activeKey}                   
                  setActiveKey={setActiveKey}
                  handleClose={handleClose}                                                                
                />              
              )
            }              
          </Tab>
        </Tabs>
      :
        <Row className="stripped">
          <Col className="col-head text-center" sm={12} lg={12}>
            {t('no-ticket-yet-create-one')}&nbsp;
            <span className="link action" onClick={() => handleTicketEdit()}>
              <AddCircleOutline color={COLOR_LINK} title={t('add-ticket')} />
            </span>              
          </Col>
        </Row>
      }      
      <TicketModal
        show={ticketModalShow}
        onHide={() => setTicketModalShow(false)}
        title={ticket?.id?t('update-ticket'):t('add-ticket')}
      >
        <TicketForm       
          ticket={ticket}
          closeAndUpdate={closeAndUpdateTicketModal}
        />
      </TicketModal>
      <UploadFile
        show={uploadModalShow}
        onHide={() => setUploadModalShow(false)}
        ticket={ticket}
        closeAndUpdate={closeAndUpdateUploadModal}
      />  
    </>
  );
}; 

export default Tickets;
