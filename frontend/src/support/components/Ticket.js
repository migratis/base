import { useTranslation } from 'react-i18next';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { 
  IoSettingsOutline as SettingsOutline, 
  IoCloseCircleOutline as CloseCircleOutline,
  IoDownloadOutline as DownloadOutline 
} from 'react-icons/io5';
import Accordion from 'react-bootstrap/Accordion';
import Threads from './Threads';
import ThreadForm from './ThreadForm';
import moment from 'moment';
import Badge from 'react-bootstrap/Badge';
import { COLOR_LINK } from '../../settings';

const Ticket = (props) => {
  const { t } = useTranslation('support');  

  return (
    <div className="border-top striped">
      <Row className="w-100">
        {/* Left pane: ticket metadata — badge top-left, actions top-right. */}
        <Col className="text-left" sm={12} lg={4}>
          <div className="d-flex justify-content-between align-items-start mb-2">
            <Badge className="badge badge-danger">
              {t('number')}: {props.ticket.id}
            </Badge>
            { props.ticket.status !== 'c' &&
              <div className="text-right">
                <span className="link action" onClick={() => props.handleTicketEdit(props.ticket.id)}>
                  <SettingsOutline color={COLOR_LINK} title={t('edit')} />
                </span>
                &nbsp;
                <span className="link action" onClick={ () => props.handleClose(props.ticket.id)}>
                  <CloseCircleOutline color={COLOR_LINK} title={t('close')} />
                </span>
              </div>
            }
          </div>
          <strong>{t('topic')}:&nbsp;</strong>{props.ticket.topic?t(props.ticket.topic.label.key):props.ticket.object}<br/>
          <strong>{t('creation-date')}:&nbsp;</strong>{moment(props.ticket.cdate).format('DD-MM-YYYY HH:mm:ss')}<br/>
          <strong>{t('modification-date')}:&nbsp;</strong>{moment(props.ticket.mdate).format('DD-MM-YYYY HH:mm:ss')}
        </Col>
        {/* Right pane: the Discussion accordion spans the full width of the pane. */}
        <Col className="text-left px-0" sm={12} lg={8}>
          <Accordion id={"accordion-" + props.ticket.id} activeKey={props.activeKey} onSelect={e => props.setActiveKey(e)}>
            <Accordion.Item eventKey={props.ticket.id}>
              <Accordion.Header as="h3"><strong>{t('discussion')}</strong></Accordion.Header>
              <Accordion.Body>
                <div>
                  <strong>{t('message-from-you')}:&nbsp;</strong>{props.ticket.content}
                </div>
                <hr/>
                { props.ticket.threads && props.ticket.threads.length > 0 && 
                  <Threads                          
                    ticket={props.ticket}
                    refresh={props.refresh}
                    setRefresh={props.setRefresh}
                    setActiveKey={props.setActiveKey}
                    handleAccordion={props.handleAccordion}                                
                  />
                }
                <Row>
                  { props.ticket.status !== 'c' &&
                    <>
                      <Col className="text-center" sm={12} lg={6}>
                        <ThreadForm                               
                          ticket={props.ticket}
                          refresh={props.refresh}
                          setRefresh={props.setRefresh}
                          setActiveKey={props.setActiveKey}                              
                          handleAccordion={props.handleAccordion}
                        />
                      </Col>                    
                    </>
                  }
                  <Col className="text-center" sm={12} lg={props.ticket.status === 'c'?12:6}>
                    { props.ticket.files.length > 0 && props.ticket.files.map(file =>
                      <Row className="border-top text-small striped" key={file.id}>
                        <Col sm={12} lg={9}>
                          {file.filename}
                        </Col>
                        <Col sm={11} lg={2}>
                          {moment(file.cdate).format('DD-MM-y')}                                      
                        </Col>
                        <Col sm={1} lg={1}>
                          <DownloadOutline 
                            onClick={() => props.handleDownload(file)} 
                            color={COLOR_LINK} 
                            title={t('download-file')} 
                            height="25px" 
                            width="25px"
                          />                            
                        </Col>
                      </Row>
                    )}
                    { props.ticket.status !== 'c' &&
                      <>
                        <div className="text-center">
                          <button onClick={() => props.handleUpload(props.ticket.id)} className="btn btn-primary btn-block btn-wide">
                            {t('upload-file')}
                          </button>
                        </div>                      
                      </>
                    }
                  </Col>
                </Row>
                <div id={"anchor-" + props.ticket.id}></div>          
              </Accordion.Body>      
            </Accordion.Item>
          </Accordion>
        </Col>
      </Row>
    </div>
  );  
};

export default Ticket;
