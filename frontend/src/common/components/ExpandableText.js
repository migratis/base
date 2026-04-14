import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const MOBILE_BREAKPOINT = 758;

/**
 * ExpandableText
 *
 * Renders a plain-text string with proper line breaks (whitespace preserved).
 * When the text exceeds `maxChars` characters it is truncated and a
 * "Show more / Show less" toggle link is displayed below.
 * On mobile (≤ 758px), uses `mobileMaxChars` instead.
 *
 * Props:
 *   text            {string}  — the text to display
 *   maxChars        {number}  — character threshold before collapsing (default 120)
 *   mobileMaxChars  {number}  — mobile threshold (default 60)
 *   ns              {string}  — i18next namespace for show-more / show-less keys
 *                             (default 'generator')
 */
const ExpandableText = ({ 
  text = '', 
  maxChars = 120, 
  mobileMaxChars = 60,
  ns = 'generator' 
}) => {
  const { t } = useTranslation(ns);
  const [expanded, setExpanded] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= MOBILE_BREAKPOINT);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (!text) return null;

  const effectiveMaxChars = isMobile ? mobileMaxChars : maxChars;
  const needsTruncation = text.length > effectiveMaxChars;
  const displayed = needsTruncation && !expanded
    ? text.slice(0, effectiveMaxChars).trimEnd() + '…'
    : text;

  return (
    <span>
      <span style={{ whiteSpace: 'pre-wrap' }}>{displayed}</span>
      {needsTruncation && (
        <>
          {' '}
          <span
            className="expandable-text-toggle"
            onClick={() => setExpanded(prev => !prev)}
          >
            {expanded ? t('show-less') : t('show-more')}
          </span>
        </>
      )}
    </span>
  );
};

export default ExpandableText;
