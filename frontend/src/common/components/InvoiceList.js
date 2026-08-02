import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import moment from 'moment';
import Badge from 'react-bootstrap/Badge';
import downloadFile from 'downloadjs';
import { IoDownloadOutline as DownloadOutline } from 'react-icons/io5';
import InvoicesService from '../services/invoices.service';
import { COLOR_LINK } from '../../settings';

/**
 * The receipts for one paying purpose.
 *
 * Account → Billing gives credits and subscription a column each, and a column
 * lists only what its own module was paid for — hence `purpose`, which is
 * filtered server-side by the payment engine. `labelNs` says where the
 * invoice's `label_key` resolves: the plan label belongs to the `subscription`
 * namespace, the credit-purchase label to the shared `billing` one.
 */
const InvoiceList = ({ purpose, labelNs = 'billing' }) => {
  const { t } = useTranslation(['billing', labelNs]);
  const [ invoices, setInvoices ] = useState(null);

  useEffect(() => {
    InvoicesService.getInvoices(purpose).then((rows) => setInvoices(rows || []));
  }, [purpose]);

  const handleDownload = (invoice) => {
    InvoicesService.download(invoice).then((response) => {
      downloadFile(
        new Blob([response]),
        'migratis-invoice-' + moment(invoice.mdate).format('DD-MM-y') + '.pdf',
        'application/pdf'
      );
    });
  };

  // Nothing at all until the first response — an empty list and a pending one
  // would otherwise both read as "no invoices".
  if (!invoices) return null;

  return (
    // The heading sits outside the scrolling box so it stays put while a long
    // history scrolls, and so the billing column can bottom-align the whole
    // block against the column beside it.
    <div className="invoice-list">
      <h6>{t('your-invoices')}</h6>
      <div className="invoices">
      { invoices.length === 0 ?
        <p className="text-muted">{t('no-invoices')}</p>
        :
        invoices.map((item) =>
          <p key={item.id}>
            {item.label_key ? t(item.label_key, { ns: labelNs }) : ''}&nbsp;
            { item.amount === 0 &&
              <span>({t('trial-period')})&nbsp;</span>
            }
            {t('of')}&nbsp;
            {moment(item.mdate).format('DD-MM-y')}&nbsp;
            {item.amount / 100}&euro;
            &nbsp;&nbsp;
            <Badge bg={item.status === "paid" ? "success" : "danger"}>
              {item.status === "paid" ? t('paid') : t('unpaid')}
            </Badge>&nbsp;&nbsp;
            { item.status === "paid" &&
              <button className="link btn btn-white" onClick={() => handleDownload(item)}>
                <DownloadOutline color={COLOR_LINK} title={t('download-invoice')} height="25px" width="25px"/>
              </button>
            }
          </p>
        )
      }
      </div>
    </div>
  );
};

export default InvoiceList;
