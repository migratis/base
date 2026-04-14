import React from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from 'react-i18next';

const Message = () => {
  const location = useLocation();  
  const { t } = useTranslation('layout');

  return (

    <div>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>{ t('message') }</h2>
          </div>
        </div>
      </header>      
      <p className="text-center"><strong>{ location.state }</strong></p>
    </div>

  );

};

export default Message;
