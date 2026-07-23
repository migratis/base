import { useState, useEffect, useCallback } from 'react';
import CreditsService from '../services/credits.service';
import StripeCheckoutModal from './StripeCheckoutModal';
import { useTranslation } from 'react-i18next';
import { IoSparklesOutline as SparkleIcon } from 'react-icons/io5';

const CreditsIndicator = ({ compact = false, dark = false }) => {
  const { t } = useTranslation('credits');
  const [usage, setUsage] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const loadUsage = useCallback(() => {
    CreditsService.getCredits().then((data) => {
      if (data) setUsage(data);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    loadUsage();
    const onCreditsChanged = () => loadUsage();
    const onStorage = (e) => {
      if (e.key === 'credits-changed') loadUsage();
    };
    window.addEventListener('credits-changed', onCreditsChanged);
    window.addEventListener('storage', onStorage);
    return () => {
      window.removeEventListener('credits-changed', onCreditsChanged);
      window.removeEventListener('storage', onStorage);
    };
  }, [loadUsage]);

  const getColor = () => {
    if (!usage) return 'var(--color-mid-gray)';
    if (usage.credits === 0) return '#dc3545';
    if (usage.credits <= 3) return 'var(--color-orange)';
    return 'var(--color-green)';
  };

  // Everyone spends credits on human-lane AI now — a subscription only covers
  // the one-time sandbox-approval charge, not AI calls (owner 2026-07-22). So
  // the counter always shows once the balance has loaded.
  if (!usage) return null;

  if (compact) {
    return (
      <>
        <div
          className="sidebar-ai-indicator"
          onClick={() => setShowModal(true)}
          title={t('click-to-buy')}
          style={dark ? { backgroundColor: '#000' } : undefined}
        >
          <SparkleIcon />
          <span
            className={`sidebar-label ai-label${dark ? ' ai-label--dark' : ''}`}
            style={dark ? { opacity: 1, transform: 'none', color: 'var(--color-light)' } : undefined}
          >{t('credits-label')}</span>
          <div className={`ai-count ${usage.credits === 0 ? 'ai-count--empty' : usage.credits <= 3 ? 'ai-count--low' : ''}`}>{usage.credits}</div>
        </div>

        <StripeCheckoutModal
          show={showModal}
          onHide={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); loadUsage(); }}
          currentUsage={usage}
        />
      </>
    );
  }

  return (
    <>
      <button
        className="btn btn-sm me-2 text-white"
        style={{ fontSize: '0.85rem', backgroundColor: getColor() }}
        onClick={() => setShowModal(true)}
        title={t('click-to-buy')}
      >
        <SparkleIcon style={{ marginRight: '6px' }} />
        {t('credits-remaining', { credits: usage.credits })}
      </button>

      <StripeCheckoutModal
        show={showModal}
        onHide={() => setShowModal(false)}
        onSuccess={() => { setShowModal(false); loadUsage(); }}
        currentUsage={usage}
      />
    </>
  );
};

export default CreditsIndicator;
