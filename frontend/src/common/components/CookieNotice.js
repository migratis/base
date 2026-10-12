import React, { useCallback, useEffect, useRef, useState } from 'react';
import Button from 'react-bootstrap/Button';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import CommonService from '../services/common.service';
import { refusableCategories } from '../tools/cookieCategories';
import {
  forgetRetiredRecords, hasDecided, onConsentChange, setConsent,
} from '../tools/cookieConsent';
import CookieChoices from './CookieChoices';

/**
 * The first-visit storage notice.
 *
 * It has two modes, and which one it takes is decided by the published
 * inventory rather than by a setting:
 *
 * **Notice** — nothing this deployment stores requires consent. It says what
 * is stored and why, links to the full list, and offers one button that
 * acknowledges having read it. It does *not* ask for permission, because
 * asking for a permission that is not needed and that nothing is gated on is
 * telling the visitor something untrue about their own choice. There is no
 * backdrop: an exempt cookie may not be made to look like a condition of
 * entry.
 *
 * **Consent** — the inventory declares at least one refusable entry. Accept,
 * refuse and choose are then offered as three buttons of the same size and
 * weight, because a refusal that is harder to reach than an acceptance is not
 * a free choice (CNIL/CNPD decisional practice; EDPB Guidelines 05/2020).
 * Nothing is recorded until one of them is pressed, and dismissing the sheet
 * records nothing — silence is not consent.
 *
 * This replaces `react-cookie-consent`, which can express neither: it offers
 * one button, no categories and no refusal, and the copy it shipped with
 * ("by continuing to visit this site you agree") is the implied consent the
 * CJEU ruled out in *Planet49* (C-673/17).
 */
export const CookieNotice = () => {
  const { t, i18n } = useTranslation('cookie');
  const [inventory, setInventory] = useState(null);
  const [visible, setVisible] = useState(!hasDecided());
  const [expanded, setExpanded] = useState(false);
  const [selected, setSelected] = useState([]);
  const sheet = useRef(null);

  // Storage this deployment no longer sets goes whether or not the visitor is
  // about to be shown anything.
  useEffect(forgetRetiredRecords, []);

  // The inventory decides whether this is a notice or a consent request, so it
  // is fetched before anything is drawn. A failure leaves it empty and the
  // notice renders in its information form: we would rather say less than
  // claim a consent mechanism we cannot drive.
  //
  // Keyed on `visible` rather than fetched once on mount: a visitor who has
  // already answered is shown nothing, and every page of the site would
  // otherwise have made a request whose answer is never rendered. It still
  // runs when /cookies erases the record, because that is when the notice
  // comes back and when the mode has to be decided again.
  useEffect(() => {
    if (!visible || inventory !== null) return undefined;
    let live = true;
    CommonService.getCookies()
      .then((response) => { if (live) setInventory(response || []); })
      .catch(() => { if (live) setInventory([]); });
    return () => { live = false; };
  }, [visible, inventory]);

  // A choice made on the /cookies page closes this, and clearing one reopens
  // it — the two surfaces are one mechanism.
  useEffect(() => onConsentChange(() => {
    setVisible(!hasDecided());
    setExpanded(false);
  }), []);

  // Opening the sheet moves focus into it, so it is reachable without a mouse
  // and announced by a screen reader. It never traps focus: in notice mode the
  // page behind it is fully usable, and that is the point.
  useEffect(() => {
    if (visible && sheet.current) sheet.current.focus();
  }, [visible]);

  // Read off the inventory's own `requires_consent`, so the mode this draws in
  // is the backend's answer rather than a second opinion about it.
  const refusable = refusableCategories(inventory);
  const asksForConsent = refusable.length > 0;

  const record = useCallback((categories) => {
    setConsent(categories, inventory);
    setVisible(false);
  }, [inventory]);

  const dismiss = useCallback(() => {
    // Only reachable in notice mode. In consent mode there is nothing to
    // dismiss to: refusing is one click and is recorded as a refusal, where
    // closing the sheet would have to be recorded as nothing at all.
    record([]);
  }, [record]);

  const onKeyDown = (event) => {
    if (event.key === 'Escape' && !asksForConsent) dismiss();
  };

  const toggle = (category, on) => {
    setSelected((current) => (
      on ? [...new Set([...current, category])] : current.filter((c) => c !== category)
    ));
  };

  if (!visible || inventory === null) return null;

  return (
    <section
      className={`cookie-notice${asksForConsent ? ' cookie-notice--consent' : ''}`}
      role="dialog"
      aria-modal="false"
      aria-labelledby="cookie-notice-title"
      tabIndex={-1}
      ref={sheet}
      onKeyDown={onKeyDown}
      lang={i18n.language}
    >
      <div className="cookie-notice-body">
        <h2 className="cookie-notice-title" id="cookie-notice-title">
          {t('notice-title')}
        </h2>
        <p className="cookie-notice-text">
          { asksForConsent ? t('notice-consent-text') : t('notice-information-text') }
        </p>
        <p className="cookie-notice-links">
          <Link to="/cookies">{t('see-everything-stored')}</Link>
        </p>

        { expanded && (
          <div className="cookie-notice-choices">
            <CookieChoices
              t={t}
              inventory={inventory}
              selected={selected}
              onChange={toggle}
              idPrefix="notice"
            />
          </div>
        )}
      </div>

      {/* Equal weight, equal size, same row. The refusal is never the quiet
          one — which is the single most-penalised cookie-banner pattern in
          the EU, and what the one-button banner this replaces was. */}
      <div className="cookie-notice-actions">
        { asksForConsent ? (
          <>
            { expanded ? (
              <Button variant="primary" onClick={() => record(selected)}>
                {t('save-my-choices')}
              </Button>
            ) : (
              <Button variant="outline-dark" onClick={() => setExpanded(true)}>
                {t('choose-what-to-allow')}
              </Button>
            )}
            <Button variant="outline-dark" onClick={() => record([])}>
              {t('refuse-everything-optional')}
            </Button>
            <Button variant="primary" onClick={() => record(refusable)}>
              {t('accept-everything-optional')}
            </Button>
          </>
        ) : (
          <Button variant="primary" onClick={dismiss}>
            {t('understood')}
          </Button>
        )}
      </div>
    </section>
  );
};

export default CookieNotice;
