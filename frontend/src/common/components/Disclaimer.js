import React from 'react';
import { useTranslation } from 'react-i18next';
import DOMPurify from 'dompurify';
import { PageShell } from './PageShell';

const Disclaimer = () => {
  const { t } = useTranslation('legal');
  return (
    <PageShell title={ t('legal-disclaimer') }>
      <h3 className="review-section">
        <span>{ t('hosting-infos-title') }</span>
      </h3>
      <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(t('hosting-infos')) }} />
      <p className="text-muted">{ t('all-right-reserved') + ' 04/09/2023' }</p>
    </PageShell>
  );

};

export default Disclaimer;
