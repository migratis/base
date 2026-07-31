// =============================================================================
// Status — a live self-check, not an uptime history.
//
// Nothing here is recorded, averaged or remembered: the page asks the backend
// how it is right now and prints the answer. That is a deliberate limit and the
// page says so, because a status page that claims a health nobody measured is
// worse than no status page at all.
//
// Three things are reported: the API answered, the database round-tripped, and
// each configured AI provider is either operational or has had its circuit
// breaker tripped — the same signal that removes it from the model picker.
// =============================================================================
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import moment from 'moment';
import CommonService from '../services/common.service';
import { LoaderIndicator } from './LoaderIndicator';
import { PageShell, PagePanel } from './PageShell';

const STATE_CLASS = {
  operational: 'status-dot--ok',
  unavailable: 'status-dot--down',
  degraded: 'status-dot--warn',
};

export const StatusLine = ({ label, state, t }) => (
  <li className="status-line">
    <span className={`status-dot ${STATE_CLASS[state] || 'status-dot--unknown'}`} />
    <span className="status-line__label">{label}</span>
    <span className="status-line__state">{t(`status-${state}`)}</span>
  </li>
);

const Status = () => {
  const { t } = useTranslation('info');
  const [report, setReport] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    CommonService.getStatus()
      .then((response) => {
        // A body without `api` is an error envelope, not a report — treating it
        // as one would paint the page green off a failure.
        if (response && response.api) setReport(response);
        else setFailed(true);
      })
      .catch(() => setFailed(true));
  }, []);

  // The request itself is the measurement: if it did not come back, the only
  // honest thing the page can say is that it could not reach the API.
  if (failed) {
    return (
      <PageShell title={t('status')} description={t('status-intro')}>
        <p className="status-unreachable">{t('status-unreachable')}</p>
      </PageShell>
    );
  }

  return (
    <PageShell title={t('status')} description={t('status-intro')} panel={false}>
      <LoaderIndicator />
      {report && (
        <>
          <PagePanel title={t('status-platform')}>
            <ul className="status-list">
              <StatusLine label={t('status-api')} state={report.api} t={t} />
              <StatusLine label={t('status-database')} state={report.database} t={t} />
            </ul>
          </PagePanel>

          {report.services.length > 0 && (
            <PagePanel title={t('status-ai-services')}>
              <p className="text-muted">{t('status-ai-services-note')}</p>
              <ul className="status-list">
                {report.services.map((service) => (
                  <StatusLine
                    key={service.code}
                    label={service.label}
                    state={service.state}
                    t={t}
                  />
                ))}
              </ul>
            </PagePanel>
          )}

          <PagePanel>
            <p className="text-muted">
              {t('status-checked-at')}:&nbsp;
              {moment(report.checked_at).format('DD-MM-YYYY HH:mm:ss')}
            </p>
            <p className="text-muted">{t('status-no-history')}</p>
          </PagePanel>
        </>
      )}
    </PageShell>
  );
};

export default Status;
