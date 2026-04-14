import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { useTranslation } from 'react-i18next';
import { IoClose as CloseIcon } from 'react-icons/io5';
import { useRef, useEffect } from 'react';

export const CommonModal = ({ closeLabel, onEntered, ...props }) => {

    const { t } = useTranslation("modal");
    const bodyRef = useRef(null);

    const scrollBodyToTop = () => {
      if (bodyRef.current) {
        bodyRef.current.scrollTop = 0;
      }
    };

    const handleEntered = () => {
      scrollBodyToTop();
      if (onEntered) {
        onEntered();
      }
    };

    useEffect(() => {
      if (!props.show) return;

      const handleResize = () => {
        scrollBodyToTop();
      };

      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }, [props.show]);

    return (
      <Modal
        {...props}
        size="lg"
        centered
        className="migratis-modal"
        onEntered={handleEntered}
      >
        <Modal.Header className="migratis-modal-header">
          {props.icon && <span className="migratis-modal-icon">{props.icon}</span>}
          <Modal.Title className="migratis-modal-title">
            {props.title}
          </Modal.Title>
          <button className="migratis-modal-close" onClick={props.onHide} aria-label="Close">
            <CloseIcon />
          </button>
        </Modal.Header>
        <Modal.Body className="migratis-modal-body" ref={bodyRef}>
          {props.children}
        </Modal.Body>
        {props.nofooter !== "true" && (
          <Modal.Footer className="migratis-modal-footer">
            <Button variant="outline-secondary" onClick={props.onHide} className="migratis-modal-btn">
              {closeLabel || t('close')}
            </Button>
          </Modal.Footer>
        )}
      </Modal>
    );
  }
