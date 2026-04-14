import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import { IoInformationCircleOutline as InfoIcon } from 'react-icons/io5';
import { useTranslation } from 'react-i18next';

/**
 * Reusable info icon with popover showing description and AI instructions.
 * 
 * @param {string} description - The description text (optional)
 * @param {string} aiInstructions - The AI instructions text (optional)
 * @param {string} placement - Popover placement: 'top', 'bottom', 'left', 'right' (default: 'auto')
 * @param {string} trigger - When to show popover: 'hover', 'focus', 'click' (default: ['hover', 'focus'])
 */
export const InfoPopover = ({ description, aiInstructions, placement = 'auto', trigger = ['hover', 'focus'] }) => {
  const { t } = useTranslation('generator');

  const hasContent = description || aiInstructions;

  if (!hasContent) {
    return null;
  }

  return (
    <OverlayTrigger
      trigger={trigger}
      placement={placement}
      flip={true}
      overlay={
        <Popover className="info-popover">
          <Popover.Body>
            {description && (
              <>
                <strong>{t('description')}:</strong> {description}
              </>
            )}
            {description && aiInstructions && <hr className="my-2" />}
            {aiInstructions && (
              <>
                <strong>{t('ai-instructions')}:</strong> {aiInstructions}
              </>
            )}
          </Popover.Body>
        </Popover>
      }
    >
      <span className="popover-trigger">
        <InfoIcon />
      </span>
    </OverlayTrigger>
  );
};

export default InfoPopover;
