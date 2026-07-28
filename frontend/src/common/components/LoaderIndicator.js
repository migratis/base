import Modal from 'react-bootstrap/Modal';
import { usePromiseTracker } from "react-promise-tracker";
import { ThreeDots } from 'react-loader-spinner';
import { COLOR_LINK } from '../../settings';

// `always` shows the spinner without a tracked promise behind it — used as the
// Suspense fallback for lazy routes, where nothing goes through
// react-promise-tracker and the page would otherwise stay blank while the
// chunk downloads.
export const LoaderIndicator = props => {
    const { promiseInProgress } = usePromiseTracker();

    return (
      (promiseInProgress || props.always) &&
      <Modal
        show={true}
        size="lg"
        backdrop={false}
        dialogClassName="loader-modal"
        centered
      >
      <Modal.Body className="text-center">
        <ThreeDots 
          height="80" 
          width="80" 
          radius="9"
          color={COLOR_LINK} 
          ariaLabel="three-dots-loading"
          wrapperStyle={{}}
          wrapperClassName="loader-container"
          visible={true}
        />
        {props.text && (
          <p className="mt-3 mb-0 text-muted">{props.text}</p>
        )}
      </Modal.Body>
    </Modal>
    );  
} 