import React from 'react';
import { useTranslation } from 'react-i18next';
import DOMPurify from 'dompurify';

const Disclaimer = () => {
  const { t } = useTranslation('legal');
  return (
    <div>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>{ t('legal-disclaimer') }</h2>
          </div>
        </div>
      </header>
      <p>
        <div className="row">
		      <div className="col-sm-1"></div>
		      <div className="col-sm-10">
			      <div>
              <h3 className="review-section">
                <span>{ t('hosting-infos-title') }</span>
              </h3>
              <div>
                { <p dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(t('hosting-infos')) }} /> }                            
              </div>
            </div>
        	  <p>{ t('all-right-reserved')  + ' 04/09/2023' }</p>
	        </div>
          <div className="col-sm-1"></div>                
        </div>        
      </p>   
    </div>
  );

};

export default Disclaimer;
