import React, { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';
import Table from 'react-bootstrap/Table';
import CommonService from '../services/common.service';

const Cookies = () => {
    const { t } = useTranslation('cookie');
    const [ allCookies, setAllCookies ] = useState([]);

    useEffect(() => {
        CommonService.getCookies().then(
            (response) => {
                var cookies = []
                response.forEach(function(item, name){
                    cookies.push({ 'name': item.name, 'provider': item.provider });
                })
                getCookies(cookies);
            }               
        );    
    }, []);
  
    var getCookies = function(cookies){
        var pairs = document.cookie.split(";");
        for (var i=0; i<pairs.length; i++){
            var pair = pairs[i].split("=");
            var name = (pair[0] + '').trim();
            // eslint-disable-next-line
            var referencedCookie = cookies.find((item) => {
                return item.name === name;
            });
            if (!referencedCookie) {
                cookies.push({ 'name': name, 'provider': "" });
            }
        }
        setAllCookies(cookies);

        return true;
    }

    return (
        <div>
          <header className="sticky-top">
            <div className="row">
              <div className="col-sm-12">
                <h2>{t('cookies-list')}</h2>
              </div>
            </div>
          </header>
          <LoaderIndicator />
          <Table striped responsive bordered hover>
            <thead>
              <tr>
                <th>{t('name')}</th>
                <th>{t('provider')}</th>
                <th>{t('description')}</th>                        
              </tr>
            </thead>
            <tbody>
              { allCookies && allCookies.map(
                item =>
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td>{item.provider}</td>
                    <td>{item.provider ? t(item.name) : ""}</td>                                
                  </tr>
              )}
            </tbody>
          </Table>
        </div>
    )
};

export default Cookies;
