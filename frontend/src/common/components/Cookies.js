import React, { useCallback, useEffect, useState } from "react";
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Table from 'react-bootstrap/Table';
import { useTranslation } from 'react-i18next';

import CommonService from '../services/common.service';
import { groupByCategory, refusableCategories } from '../tools/cookieCategories';
import { flag } from '../tools/featureFlag';
import {
  clearConsent, getConsent, hasConsent, setConsent,
} from '../tools/cookieConsent';
import { LoaderIndicator } from './LoaderIndicator';
import CookieChoices from './CookieChoices';
import { PageShell, PagePanel } from './PageShell';

/**
 * The published inventory of what this site stores on the visitor's device,
 * and the place a recorded choice is changed or withdrawn.
 *
 * What it publishes is decided by the backend and is the same for every
 * reader. It used to merge whatever `document.cookie` happened to hold into
 * the same table, with an empty provider and an empty purpose — so a legal
 * disclosure read differently per visitor and listed entries it could not
 * explain. A cookie we do not declare is a bug in `seed_cookies`, not a row
 * to improvise on a published page.
 *
 * The page covers localStorage and sessionStorage too, because ePrivacy
 * Article 5(3) is about storage on terminal equipment rather than about
 * cookies, and the language this site remembers has always lived in
 * localStorage.
 */
const Cookies = () => {
    const { t } = useTranslation('cookie');
    const [ inventory, setInventory ] = useState([]);
    const [ loaded, setLoaded ] = useState(false);
    const [ selected, setSelected ] = useState([]);
    const [ saved, setSaved ] = useState(null);

    useEffect(() => {
        let live = true;
        CommonService.getCookies()
            .then((response) => {
                if (!live) return;
                setInventory(response || []);
                setLoaded(true);
            })
            .catch(() => { if (live) setLoaded(true); });
        return () => { live = false; };
    }, []);

    // What the inventory says is refusable, not what this file guesses.
    const refusable = refusableCategories(inventory);

    // The switches open on what is allowed right now, so the panel is a
    // statement of the current position before it is a form.
    useEffect(() => {
        setSelected(refusableCategories(inventory).filter(hasConsent));
    }, [inventory]);
    const decided = getConsent();

    const save = useCallback(() => {
        setConsent(selected, inventory);
        setSaved('saved');
    }, [selected, inventory]);

    const withdraw = useCallback(() => {
        clearConsent(inventory);
        setSaved('cleared');
    }, [inventory]);

    const toggle = (category, on) => {
        setSaved(null);
        setSelected((current) => (
            on ? [...new Set([...current, category])] : current.filter((c) => c !== category)
        ));
    };

    // The singular is a separate key rather than i18next's `_one` suffix:
    // `seed_translations` stores one text per key per language and knows
    // nothing about plural categories. See the `cookie` namespace.
    const retention = (item) => {
        const count = item.retention_value;
        if (count === null || count === undefined) {
            return t(`retention-${item.retention_unit}`);
        }
        const key = `retention-${item.retention_unit}${count === 1 ? '-one' : ''}`;
        return t(key, { count });
    };

    return (
        <PageShell title={t('cookies')} description={t('storage-intro')} width="wide" panel={false}>
          <LoaderIndicator />

          {/* The choice panel comes first: a visitor who followed the footer
              link to change their mind should not have to read an inventory
              to find the control. Article 7(3) — as easy to withdraw as to
              give. */}
          <PagePanel>
            <h2 className="cookie-section-title">{t('your-choice')}</h2>
            { refusable.length === 0 ? (
                <p className="cookie-section-text">{t('nothing-to-consent-to')}</p>
            ) : (
                <p className="cookie-section-text">{t('what-you-can-refuse')}</p>
            )}

            { refusable.length > 0 && (
                <CookieChoices
                  t={t}
                  inventory={inventory}
                  selected={selected}
                  onChange={toggle}
                  idPrefix="page"
                />
            )}

            { saved && (
                <Alert variant="success" className="cookie-choice-feedback">
                    {t(saved === 'saved' ? 'choices-saved' : 'choice-cleared')}
                </Alert>
            )}

            <div className="form-actions">
                { refusable.length > 0 && (
                    <Button variant="primary" onClick={save}>
                        {t('save-my-choices')}
                    </Button>
                )}
                <Button
                  variant="outline-dark"
                  onClick={withdraw}
                  disabled={!decided}
                >
                    {t('withdraw-my-choice')}
                </Button>
            </div>
            <p className="cookie-section-note">
                { decided
                    ? t('choice-recorded', { date: new Date(decided.decidedAt).toLocaleString() })
                    : t('choice-not-recorded') }
            </p>
          </PagePanel>

          {/* One table per purpose. A single flat table made the reader work
              out which rows they could refuse; the heading now says it. */}
          { groupByCategory(inventory).map(({ category, entries }) => (
            <PagePanel key={category}>
              <h2 className="cookie-section-title">{t(`category-${category}`)}</h2>
              <p className="cookie-section-text">
                {t(`category-${category}-help`)}
              </p>
              <Table striped responsive bordered hover className="cookie-table">
                <thead>
                  <tr>
                    <th>{t('name')}</th>
                    <th>{t('stored-as')}</th>
                    <th>{t('retention')}</th>
                    <th>{t('provider')}</th>
                    <th>{t('description')}</th>
                  </tr>
                </thead>
                <tbody>
                  { entries.map(item => (
                    <tr key={`${item.storage}-${item.name}`}>
                      <td><code>{item.name}</code></td>
                      <td>{t(`stored-as-${item.storage}`)}</td>
                      <td>{retention(item)}</td>
                      <td>{item.provider}</td>
                      <td>{t(item.name)}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </PagePanel>
          ))}

          { loaded && inventory.length === 0 && (
            <PagePanel>
              <p className="cookie-section-text">{t('inventory-unavailable')}</p>
            </PagePanel>
          )}

          {/* Said out loud because the previous inventory declared two Stripe
              cookies this site has never set: payment runs on Stripe's own
              pages, so Stripe's cookies are set there and disclosed there.

              The "nothing is tracking you" sentence is DERIVED from the
              inventory rather than asserted. This file is mirrored into the
              base template and ships under somebody else's brand: printed
              unconditionally on a deployment that has added an analytics
              entry, it would be a false disclosure in their name. It appears
              only while the inventory supports it. */}
          <PagePanel>
            <h2 className="cookie-section-title">{t('third-parties')}</h2>
            { loaded && inventory.length > 0 && refusable.length === 0 &&
                <p className="cookie-section-text">{t('no-third-party-tracking')}</p>
            }
            { flag('SUBSCRIPTION') &&
                <p className="cookie-section-text">{t('payment-on-stripe-pages')}</p>
            }
            <p className="cookie-section-note">{t('browser-settings-note')}</p>
          </PagePanel>
        </PageShell>
    )
};

export default Cookies;
