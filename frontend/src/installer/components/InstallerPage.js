import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import InstallerService from '../services/installer.service';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';

const STEPS = { CONNECT: 'connect', TFA: 'tfa', SELECT: 'select', INSTALL: 'install' };

const InstallerPage = () => {
  const { t } = useTranslation('installer');

  // Backend-driven on/off switch (null = still checking).
  const [enabled, setEnabled] = useState(null);

  const [step, setStep]       = useState(STEPS.CONNECT);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  // Connect form
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [url, setUrl]           = useState('');

  // Two-factor step
  const [tfaEmail, setTfaEmail] = useState('');
  const [tfaCode, setTfaCode]   = useState('');

  // App list
  const [apps, setApps]               = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);

  // Install result
  const [result, setResult] = useState(null);

  // Installed modules
  const [installed, setInstalled]           = useState([]);
  const [uninstalling, setUninstalling]     = useState(null);
  const [uninstallResult, setUninstallResult] = useState(null);

  const fetchInstalled = useCallback(() => {
    InstallerService.listInstalled()
      .then((data) => setInstalled(data.modules || []))
      .catch(() => {});
  }, []);

  // Ask the backend whether the installer is enabled, then load state on mount.
  useEffect(() => {
    // The installer is a public page that manages its own connection to the
    // remote migratis instance, so it must not inherit the app's stale
    // "session expired" state (which would pop the login modal on load).
    localStorage.removeItem('session_expired');
    InstallerService.getStatus()
      .then((data) => {
        const on = data?.enabled !== false;
        setEnabled(on);
        if (!on) return;
        fetchInstalled();
        InstallerService.getSession()
          .then((session) => {
            if (session.connected) fetchApps();
          })
          .catch(() => {});
      })
      // If the status check itself fails, fall back to enabled and let the
      // normal flow surface any backend error.
      .catch(() => setEnabled(true));
  }, [fetchInstalled]);

  const fetchApps = () => {
    setLoading(true);
    setError('');
    InstallerService.listApps()
      .then((data) => {
        setApps(data.apps || []);
        setStep(STEPS.SELECT);
      })
      .catch(() => setError('connection-failed'))
      .finally(() => setLoading(false));
  };

  const handleConnect = (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    InstallerService.connect(email, password, url || undefined)
      .then((data) => {
        // The axios interceptor resolves (not rejects) on error responses, so a
        // failed connect arrives here as data without a `user`. Surface its error.
        if (data?.tfa_required) {
          setTfaEmail(data.email || email);
          setTfaCode('');
          setStep(STEPS.TFA);
          setLoading(false);
          return;
        }
        if (data?.user) {
          fetchApps();
          return;
        }
        const detail = data?.detail;
        const msg = detail?.[0]?.credentials?.[0]
          || detail?.[0]?.url?.[0]
          || detail?.[0]?.form?.[0]
          || 'connection-failed';
        setError(msg);
        setLoading(false);
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        const msg = detail?.[0]?.credentials?.[0]
          || detail?.[0]?.url?.[0]
          || detail?.[0]?.form?.[0]
          || 'connection-failed';
        setError(msg);
        setLoading(false);
      });
  };

  const handleTfa = (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    InstallerService.verifyTfa(tfaEmail, tfaCode)
      .then((data) => {
        if (data?.user) {
          fetchApps();
          return;
        }
        const detail = data?.detail;
        const msg = detail?.[0]?.code?.[0]
          || detail?.[0]?.url?.[0]
          || 'tfa-code-invalid';
        setError(msg);
        setLoading(false);
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        const msg = detail?.[0]?.code?.[0]
          || detail?.[0]?.url?.[0]
          || 'tfa-code-invalid';
        setError(msg);
        setLoading(false);
      });
  };

  const handleTfaCancel = () => {
    setStep(STEPS.CONNECT);
    setTfaCode('');
    setError('');
  };

  const handleDisconnect = () => {
    InstallerService.disconnect().finally(() => {
      setStep(STEPS.CONNECT);
      setApps([]);
      setSelectedApp(null);
      setResult(null);
      setError('');
    });
  };

  const handleInstall = () => {
    if (!selectedApp) return;
    setLoading(true);
    setError('');
    InstallerService.install(selectedApp.id)
      .then((data) => {
        setResult(data);
        setStep(STEPS.INSTALL);
        fetchInstalled();
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        const msg = detail?.[0]?.install?.[0] || detail?.[0]?.download?.[0] || 'install-failed';
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  const handleUninstall = (module) => {
    if (!window.confirm(t('confirm-uninstall', { module }))) return;
    setUninstalling(module);
    setUninstallResult(null);
    InstallerService.uninstall(module)
      .then((data) => {
        setUninstallResult(data);
        fetchInstalled();
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        const msg = detail?.[0]?.uninstall?.[0] || detail?.[0]?.module?.[0] || 'uninstall-failed';
        setUninstallResult({ success: false, error: msg });
      })
      .finally(() => setUninstalling(null));
  };

  // Still checking the backend switch.
  if (enabled === null) return <LoaderIndicator />;

  // Installer disabled on the backend — explain how to turn it back on.
  if (enabled === false) {
    return (
      <div className="container mt-4" style={{ maxWidth: 720 }}>
        <h2 className="mb-4">{t('installer-title')}</h2>
        <div className="card p-4">
          <div className="alert alert-warning mb-3">{t('installer-disabled')}</div>
          <p className="mb-2">{t('installer-disabled-set')}</p>
          <pre className="bg-light p-2 rounded mb-3">INSTALLER=True</pre>
          <p className="mb-2">{t('installer-disabled-restart')}</p>
          <pre className="bg-light p-2 rounded mb-0">docker restart backend-base-api-1</pre>
        </div>
      </div>
    );
  }

  if (loading) return <LoaderIndicator />;

  return (
    <div className="container mt-4" style={{ maxWidth: 720 }}>
      <h2 className="mb-4">{t('installer-title')}</h2>

      {/* ── Uninstall result ─────────────────────────────────────────────── */}
      {uninstallResult && (
        <div className="card p-4 mb-4">
          <h5 className="mb-3">{t('uninstall-result')}</h5>
          <div className={`alert ${uninstallResult.success ? 'alert-success' : 'alert-danger'} mb-3`}>
            {uninstallResult.success
              ? <>
                  {t('uninstalled-success', { module: uninstallResult.module })}{' '}
                  {uninstallResult.migrate_ok
                    ? t('migrations-reverted')
                    : t('migration-revert-failed')}
                  {!uninstallResult.migrate_ok && uninstallResult.migrate_output && (
                    <pre className="bg-light p-2 mt-2 small mb-0" style={{ maxHeight: 120, overflow: 'auto' }}>
                      {uninstallResult.migrate_output}
                    </pre>
                  )}
                  {uninstallResult.restart_required && (
                    <div className="mt-2 small">
                      {t('restart-to-complete-removal')}
                      <pre className="mb-0 mt-1 bg-white p-2 rounded">docker restart backend-base-api-1</pre>
                    </div>
                  )}
                </>
              : `${t('error-label')}: ${t(uninstallResult.error)}`}
          </div>
          <button
            className="btn btn-secondary"
            onClick={() => {
              setUninstallResult(null);
              setResult(null);
              setSelectedApp(null);
              setStep(apps.length > 0 ? STEPS.SELECT : STEPS.CONNECT);
            }}
          >
            {t('back')}
          </button>
        </div>
      )}

      {/* ── Installed modules ────────────────────────────────────────────── */}
      {installed.length > 0 && (
        <div className="card p-4 mb-4">
          <h5 className="mb-3">{t('installed-modules')}</h5>
          <ul className="list-group">
            {installed.map((mod) => (
              <li key={mod} className="list-group-item d-flex justify-content-between align-items-center">
                <code>{mod}</code>
                <button
                  className="btn btn-sm btn-outline-danger"
                  disabled={uninstalling === mod}
                  onClick={() => handleUninstall(mod)}
                >
                  {uninstalling === mod ? t('uninstalling') : t('uninstall')}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Step 1: Connect ──────────────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.CONNECT && (
        <div className="card p-4">
          <h5 className="mb-3">{t('connect-to-migratis')}</h5>
          {error && <div className="alert alert-danger">{t(error)}</div>}
          <form onSubmit={handleConnect}>
            <div className="mb-3">
              <label className="form-label">{t('email')}</label>
              <input
                type="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">{t('password')}</label>
              <input
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">
                {t('migratis-url')}{' '}
                <small className="text-muted">{t('leave-blank-default')}</small>
              </label>
              <input
                type="url"
                className="form-control"
                placeholder="http://host.docker.internal:8000"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary">
              {t('connect')}
            </button>
          </form>
        </div>
      )}

      {/* ── Step 1b: Two-factor code ─────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.TFA && (
        <div className="card p-4">
          <h5 className="mb-3">{t('tfa-title')}</h5>
          {error && <div className="alert alert-danger">{t(error)}</div>}
          <p className="mb-3">{t('tfa-help', { email: tfaEmail })}</p>
          <form onSubmit={handleTfa}>
            <div className="mb-3">
              <label className="form-label">{t('tfa-code')}</label>
              <input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                className="form-control"
                value={tfaCode}
                onChange={(e) => setTfaCode(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="d-flex gap-2">
              <button type="submit" className="btn btn-primary">
                {t('tfa-verify')}
              </button>
              <button type="button" className="btn btn-outline-secondary" onClick={handleTfaCancel}>
                {t('back')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── Step 2: Select app ───────────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.SELECT && (
        <div className="card p-4">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="mb-0">{t('select-app')}</h5>
            <button className="btn btn-sm btn-outline-secondary" onClick={handleDisconnect}>
              {t('disconnect')}
            </button>
          </div>
          {error && <div className="alert alert-danger">{t(error)}</div>}
          {apps.length === 0 ? (
            <div className="alert alert-info">{t('no-apps')}</div>
          ) : (
            <div className="list-group mb-3">
              {apps.map((app) => {
                const alreadyInstalled = installed.includes(app.module);
                return (
                  <button
                    key={app.id}
                    type="button"
                    className={`list-group-item list-group-item-action${selectedApp?.id === app.id ? ' active' : ''}${alreadyInstalled ? ' list-group-item-success' : ''}`}
                    onClick={() => !alreadyInstalled && setSelectedApp(app)}
                    disabled={alreadyInstalled}
                  >
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <strong>{app.name}</strong>
                        <span className="ms-2 text-muted small">{t('module-label')} {app.module}</span>
                      </div>
                      {alreadyInstalled && (
                        <span className="badge bg-success">{t('installed-badge')}</span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          <button
            className="btn btn-primary"
            disabled={!selectedApp || installed.includes(selectedApp?.module)}
            onClick={handleInstall}
          >
            {t('install-selected')}
          </button>
        </div>
      )}

      {/* ── Step 3: Result ───────────────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.INSTALL && result && (
        <div className="card p-4">
          <div className={`alert ${result.success ? 'alert-success' : 'alert-danger'} mb-3`}>
            {result.success
              ? t('installed-success', { module: result.module })
              : t('install-failed-msg')}
          </div>

          <div className="mb-3">
            <strong>{t('backend-migration')}</strong>{' '}
            {result.migrate_deferred
              ? <span className="text-info">{t('applied-on-restart')}</span>
              : <span className={result.migrate_ok ? 'text-success' : 'text-danger'}>{result.migrate_ok ? t('ok') : t('failed')}</span>
            }
            {!result.migrate_deferred && result.migrate_output && (
              <pre className="bg-light p-2 mt-1 small" style={{ maxHeight: 150, overflow: 'auto' }}>
                {result.migrate_output}
              </pre>
            )}
          </div>

          <div className="mb-3">
            <strong>{t('seed-translations')}</strong>{' '}
            {result.migrate_deferred
              ? <span className="text-info">{t('applied-on-restart')}</span>
              : <span className={result.seed_ok ? 'text-success' : 'text-danger'}>{result.seed_ok ? t('ok') : t('failed')}</span>
            }
            {!result.migrate_deferred && result.seed_output && (
              <pre className="bg-light p-2 mt-1 small" style={{ maxHeight: 100, overflow: 'auto' }}>
                {result.seed_output}
              </pre>
            )}
          </div>

          <div className="mb-3">
            <strong>{t('frontend-files')}</strong>{' '}
            <span className={result.frontend_ok ? 'text-success' : 'text-warning'}>
              {result.frontend_ok ? t('installed-automatically') : t('not-applied-volume')}
            </span>
          </div>

          {result.restart_required && (
            <div className="alert alert-warning">
              <strong>{t('almost-done')}</strong> {t('restart-to-load-module')}
              <pre className="mb-2 mt-2 small bg-white p-2 rounded">docker restart backend-base-api-1</pre>
              {t('rebuild-static-assets')}
              <pre className="mb-0 mt-2 small bg-white p-2 rounded">npm run build</pre>
            </div>
          )}

          <button
            className="btn btn-secondary"
            onClick={() => {
              setStep(STEPS.SELECT);
              setResult(null);
              setSelectedApp(null);
            }}
          >
            {t('install-another')}
          </button>
        </div>
      )}
    </div>
  );
};

export default InstallerPage;
