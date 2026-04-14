import Modal from 'react-bootstrap/Modal';

export const BlockedModal = (props) => {

    return (
      <Modal
        {...props}
        backdrop="static"
        keyboard={false}
        size="lg"
        centered
        className="migratis-modal"
      >
        <Modal.Header className="migratis-modal-header">
          <Modal.Title className="migratis-modal-title">
            {props.title}
          </Modal.Title>
          {props.showCloseButton !== false && (
            <button className="migratis-modal-close" onClick={props.onHide}>
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 512 512"><path fill="currentColor" d="M400 145.7L366.3 112L256 222.7L145.7 112L112 145.7l110.3 110.3L112 366.3l33.7 33.7L256 333.3l110.3 110.3L400 366.3L289.7 256z"/></svg>
            </button>
          )}
        </Modal.Header>
        <Modal.Body className="migratis-modal-body">
          { props.nocontainer==="true" ?
            props.children
          :
            <>
              {props.children}
            </>
          }
        </Modal.Body>
      </Modal>
    );
  }
