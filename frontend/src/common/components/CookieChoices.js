import React from 'react';
import Form from 'react-bootstrap/Form';

import {
  CATEGORY_ORDER, NECESSARY, entryRequiresConsent,
} from '../tools/cookieCategories';

/**
 * The per-category switches, shown inside the first-visit notice and again on
 * the /cookies page.
 *
 * One component for both because they are the same control: GDPR Article 7(3)
 * requires withdrawing a consent to be as easy as giving it, and the cheapest
 * way to be sure of that is for the two surfaces to be literally the same
 * switches reading the same inventory.
 *
 * `necessary` is rendered as a disabled, always-on row rather than left out.
 * A visitor is entitled to see what is stored without their permission and
 * why it does not need it — a list that only shows the optional half reads as
 * if the rest were not happening.
 */
export const CookieChoices = ({ t, inventory, selected, onChange, idPrefix = 'cc' }) => {
  const present = CATEGORY_ORDER.filter(
    (category) => category === NECESSARY
      || (inventory || []).some((item) => item.category === category)
  );
  // Refusable per the published inventory. A category with no entries in it
  // can only be `necessary` (the row above keeps that one unconditionally),
  // which is always exempt.
  const refusable = (category) => (inventory || []).some(
    (item) => item.category === category && entryRequiresConsent(item)
  );

  return (
    <ul className="cookie-choices">
      { present.map((category) => {
        const optional = refusable(category);
        const count = (inventory || []).filter(
          (item) => item.category === category
        ).length;
        const checked = optional ? (selected || []).includes(category) : true;
        const id = `${idPrefix}-${category}`;

        return (
          <li className="cookie-choice" key={category}>
            <Form.Check
              type="switch"
              id={id}
              checked={checked}
              disabled={!optional}
              onChange={(event) => onChange(category, event.target.checked)}
              label={
                <span className="cookie-choice-label">
                  <span className="cookie-choice-name">{t(`category-${category}`)}</span>
                  <span className="cookie-choice-state">
                    { optional
                        ? t('requires-consent')
                        : t('always-active') }
                  </span>
                </span>
              }
            />
            <p className="cookie-choice-help">
              {t(`category-${category}-help`)}
              { count > 0 && ' ' }
              { count > 0 && (
                <span className="cookie-choice-count">
                  {t(count === 1 ? 'entries-stored-one' : 'entries-stored', { count })}
                </span>
              )}
            </p>
          </li>
        );
      })}
    </ul>
  );
};

export default CookieChoices;
