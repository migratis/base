import React from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from 'react-i18next';
import { PageShell } from './PageShell';

const Message = () => {
  const location = useLocation();  
  const { t } = useTranslation('layout');

  return (

    <PageShell title={ t('message') } width="form">
      <p className="page-message"><strong>{ location.state }</strong></p>
    </PageShell>

  );

};

export default Message;
