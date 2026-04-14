import { useState, useEffect } from 'react';
import Modal from 'react-bootstrap/Modal';
import Badge from 'react-bootstrap/Badge';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import GeneratorService from '../../generator/services/generator.service';
import { useTranslation } from 'react-i18next';
import { IoCartOutline as CartIcon } from 'react-icons/io5';

const StripeCheckoutModal = ({ show, onHide, onSuccess, currentUsage }) => {
  const { t } = useTranslation('generator');
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTier, setSelectedTier] = useState(null);
  const [customQuantity, setCustomQuantity] = useState(100);

  const isLimitReached = (currentUsage?.credits ?? 1) <= 0;

  // Get the rate from the third tier (index 2) for custom calculation
  const thirdTier = tiers.length > 2 ? tiers[2] : null;
  const ratePerCall = thirdTier ? parseFloat(thirdTier.price) / thirdTier.extra_amount : 0.2999;

  useEffect(() => {
    if (show) {
      GeneratorService.getAIUsageTiers().then((data) => {
        setTiers(Array.isArray(data) ? data : (data?.items ?? []));
      }).catch(() => setTiers([]));
      setSelectedTier(null);
      setCustomQuantity(100);
    }
  }, [show]);

  const customMin = thirdTier?.extra_amount || 100;
  const parsedCustomQty = parseInt(customQuantity, 10);
  const customQtyValid = !isNaN(parsedCustomQty) && parsedCustomQty >= customMin;
  const isCustomTierSelected = selectedTier === tiers.length - 1 && tiers.length > 0;
  const canPurchase = selectedTier !== null && (!isCustomTierSelected || customQtyValid);

  const handlePurchase = async () => {
    if (!canPurchase) return;
    setLoading(true);
    try {
      const response = await GeneratorService.purchaseExtraCalls(selectedTier, isCustomTierSelected ? parsedCustomQty : undefined);
      if (response?.checkout_url) {
        window.location.href = response.checkout_url;
      }
    } catch (error) {
      console.error('Purchase error:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateCustomPrice = () => {
    if (isNaN(parsedCustomQty) || parsedCustomQty <= 0) return '0.00';
    return (parsedCustomQty * ratePerCall).toFixed(2);
  };

  const handleQuantityChange = (e) => {
    const value = e.target.value;
    // Allow empty string or positive digits only — store as raw string so the
    // user can type sequentially (e.g. erase then type 4 → 40 → 400)
    if (value === '' || /^\d+$/.test(value)) {
      setCustomQuantity(value);
    }
  };

  const handleQuantityBlur = () => {
    // On blur, snap up to minimum if the entered value is below it
    if (isNaN(parsedCustomQty) || parsedCustomQty < customMin) {
      setCustomQuantity(String(customMin));
    }
  };

  return (
    <Modal show={show} onHide={onHide} centered className="migratis-modal">
      <Modal.Header className="migratis-modal-header">
        <span className="migratis-modal-icon"><CartIcon /></span>
        <Modal.Title className="migratis-modal-title">{t('purchase-extra-calls')}</Modal.Title>
        <button className="migratis-modal-close" onClick={onHide}>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 512 512"><path fill="currentColor" d="M400 145.7L366.3 112L256 222.7L145.7 112L112 145.7l110.3 110.3L112 366.3l33.7 33.7L256 333.3l110.3 110.3L400 366.3L289.7 256z"/></svg>
        </button>
      </Modal.Header>
      <Modal.Body className="migratis-modal-body">
        {isLimitReached && <p className="mb-3">{t('ai-limit-reached-description')}</p>}

        <div className="text-center mb-4">
          <Badge
            bg={isLimitReached ? 'danger' : (currentUsage?.credits <= 3 ? 'warning' : 'success')}
            style={{ fontSize: '1rem', padding: '8px 16px' }}
          >
            {t('ai-calls', { remaining: currentUsage?.credits || 0 })}
          </Badge>
        </div>

        <div className="d-flex flex-column gap-2">
          {tiers.map((tier, index) => {
            const isLastTier = index === tiers.length - 1;
            
            return (
              <div
                key={index}
                className={`border rounded p-3 ${selectedTier === index ? 'border-primary bg-light' : ''}`}
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  borderColor: selectedTier === index ? 'var(--color-primary)' : 'var(--color-border)',
                }}
                onClick={() => setSelectedTier(index)}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--color-primary)'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = selectedTier === index ? 'var(--color-primary)' : 'var(--color-border)'}
              >
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    {!isLastTier && (
                      <>
                        <strong>{tier.extra_amount} {t('extra-ai-calls')}</strong>
                        <div className="text-muted small">
                          {t('price-per-call', { price: (tier.price / tier.extra_amount).toFixed(2) })}
                        </div>
                      </>
                    )}
                    {isLastTier && (
                      <>
                        <InputGroup onClick={(e) => e.stopPropagation()}>
                          <Form.Control
                            type="text"
                            inputMode="numeric"
                            value={customQuantity}
                            onChange={handleQuantityChange}
                            onBlur={handleQuantityBlur}
                            isInvalid={customQuantity !== '' && !customQtyValid}
                            style={{ maxWidth: '150px' }}
                          />
                          <InputGroup.Text style={{ fontWeight: 'bold' }}>{t('extra-ai-calls')}</InputGroup.Text>
                        </InputGroup>
                        <div className="text-muted small mt-1">
                          {customQtyValid
                            ? t('price-per-call', { price: ratePerCall.toFixed(2) })
                            : t('minimum-quantity', { min: customMin })}
                        </div>
                      </>
                    )}
                  </div>
                  <div className="text-end">
                    <Badge bg="success" style={{ fontSize: '1rem' }}>
                      €{isLastTier ? calculateCustomPrice() : tier.price}
                    </Badge>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Modal.Body>
      <Modal.Footer className="migratis-modal-footer">
        <button className="btn btn-outline-secondary migratis-modal-btn" onClick={onHide}>
          {t('cancel')}
        </button>
        <button
          className="btn migratis-modal-btn"
          disabled={loading || !canPurchase}
          onClick={handlePurchase}
          style={{ backgroundColor: 'var(--color-primary)', borderColor: 'var(--color-primary)', color: 'white' }}
        >
          {loading ? t('loading') : t('buy-now')}
        </button>
      </Modal.Footer>
    </Modal>
  );
};

export default StripeCheckoutModal;
