import React, { useState } from "react";
import { useTranslation } from 'react-i18next';
import { IoPencil as Pencil } from 'react-icons/io5';
import { CommonModal as ThreadModal } from '../../common/modals/CommonModal';
import ThreadForm from './ThreadForm';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import moment from 'moment';
import { COLOR_LINK } from "../../settings";

const Threads = (props) => {
  const { t } = useTranslation('support');
  const [ thread, setThread ] = useState(null);
  const [ threadModalShow, setThreadModalShow ] = useState(false)

  const handleThreadEdit = (threadId) => {
    if (threadId) {
      setThread(props.ticket.threads.find((elem) => {
        return elem.id === threadId;
      }));      
      setThreadModalShow(true);  
    } 
  };

  const closeAndUpdateThreadModal = () => {
    setThreadModalShow(false);
    props.setRefresh(!props.refresh);
    props.setActiveKey(props.ticket.id);
    props.handleAccordion(props.ticket.id);
  }

  return (
    <div>
      <Container>
        { props.ticket && props.ticket.threads.map(
          (item, index) =>
            <div key={index}>
              <Row>
                <Col className={item.user && item.replier && item.replier !== item.user ?"text-left alert alert-danger":"text-left alert alert-info"} sm={11} lg={11}>
                  <Row>
                    <Col>
                      <strong>{t('creation-date')}:&nbsp;</strong>{moment(item.cdate).format('DD-MM-YYYY HH:mm:ss')}<br/>
                      <strong>{t('modification-date')}:&nbsp;</strong>{moment(item.mdate).format('DD-MM-YYYY HH:mm:ss')}<br/>
                      <strong>{item.user && item.replier && item.replier !== item.user ?t('our-answer'):t('message-from-you')}:&nbsp;</strong>{item.content}
                    </Col>
                  </Row>
                </Col>
                { (!item.replier || item.replier === item.user) && !item.replied && props.ticket.status !== 'c' &&
                  <Col className="text-left" sm={1} lg={1}>
                    <span className="link action" onClick={() => handleThreadEdit(item.id)}>
                      <Pencil color={COLOR_LINK} title={t('edit')} />
                    </span> 
                  </Col>                  
                }                                   
              </Row>
            </div>          
        )} 
      </Container>
      <ThreadModal
        show={threadModalShow}
        onHide={() => setThreadModalShow(false)}
        title={t('update-thread')}
      >
        <ThreadForm  
          thread={ thread }
          ticket={ props.ticket }
          closeAndUpdate={ closeAndUpdateThreadModal }
        />
      </ThreadModal>   
      <hr/>
    </div>
  );
}; 

export default Threads;