import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import SubscriptionService from '../services/subscription.service';
import Table from 'react-bootstrap/Table';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';

const Pricing = () => {
  const { t } = useTranslation('subscription');  
  const [ plans, setPlans ] = useState([]);

  useEffect(() => {
    SubscriptionService.getPlans().then(
        (response) => {
          setPlans(response);
        }
    );
  }, []);
  
  return (
    <>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>
              {t('pricing')}
            </h2> 
          </div>
        </div>
      </header>   
      <p className="card card-success">
        {t("trial-explanation")}
      </p>
      <LoaderIndicator />
      <Table striped responsive bordered hover>
        <thead>
          <tr>
            <th className="text-left">{t('label')}</th>
            <th className="text-left">{t('price')}&nbsp;{t('ttc')}</th>
          </tr>
        </thead>
        <tbody>
          { (plans && plans.length>0) ? plans.map(
            item => 
              <tr key={item.id}>
                <td className="text-left">{t(item.label.key)}&nbsp;{t('with-trial')}</td>
                <td className="text-left">{item.price}&nbsp;€</td>
              </tr> 
            )
          :
            <tr>
              <td colSpan="3" className="text-center">
                {t('no-plans-for-the-moment')}           
              </td>
            </tr>
          }
        </tbody>
      </Table>
    </>
  );
}; 

export default Pricing;
