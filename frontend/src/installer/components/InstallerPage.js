import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import InstallerService from '../services/installer.service';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';

const STEPS = {
  CONNECT: 'connect', TFA: 'tfa', SELECT: 'select', CONFIG: 'config', INSTALL: 'install',
  UPGRADE_PREVIEW: 'upgrade-preview', UPGRADE_RESULT: 'upgrade-result',
};

const EMPTY_CONFIG = {
  admin:  { email: '', password: '' },
  email:  { EMAIL_HOST: '', EMAIL_HOST_USER: '', EMAIL_HOST_PASSWORD: '', EMAIL_SENDER: '', EMAIL_MODERATOR: '' },
  stripe: { STRIPE_API_KEY: '', STRIPE_SECRET_KEY: '', STRIPE_WEBHOOK_SECRET_KEY: '' },
};

// Which config groups an app needs, derived from its modules_needed.
const requiredGroups = (app) => {
  const mods = app?.modules_needed || [];
  return { user: mods.includes('user'), subscription: mods.includes('subscription') };
};

// The axios interceptor resolves (not rejects) error responses, so a dead
// upstream session arrives in `.then` as a payload carrying this signal. The
// backend clears the stale cookies and returns it whenever the Migratis session
// is no longer alive, so the UI can drop back to the login form.
const isDisconnected = (payload) => payload?.detail?.[0]?.session?.[0] === 'not-connected';

// After an install/uninstall writes files into the mounted frontend, the CRA dev
// server recompiles — and a module_registry.js change forces a full page reload,
// which would wipe the in-memory result. Persist it so the reloaded page can
// restore and show it. A short TTL prevents a stale result resurfacing later.
// How the frontend is served, baked in by CRA at build time:
//   `react-scripts start` (hot-reload dev container) → 'development'
//   `react-scripts build` (static bundle served by nginx) → 'production'
// In dev a written file auto-recompiles, so we wait for the rebuild; in
// production the change needs `npm run build`, so there is nothing to wait for.
const IS_DEV = process.env.NODE_ENV === 'development';

const PENDING_KEY = 'installer_pending_result';
const PENDING_TTL = 60000;

const persistPending = (payload) => {
  try { localStorage.setItem(PENDING_KEY, JSON.stringify({ ...payload, ts: Date.now() })); } catch (_) {}
};
const readPending = () => {
  try {
    const raw = localStorage.getItem(PENDING_KEY);
    if (!raw) return null;
    const p = JSON.parse(raw);
    if (!p || (Date.now() - (p.ts || 0)) > PENDING_TTL) {
      localStorage.removeItem(PENDING_KEY);
      return null;
    }
    return p;
  } catch (_) { return null; }
};
const clearPending = () => { try { localStorage.removeItem(PENDING_KEY); } catch (_) {} };

// Resolve once the webpack dev server finishes the recompile triggered by the
// freshly written module files. Listens to the WDS socket (an `invalid` recompile
// start followed by `ok`/`hash`) and falls back to a bounded timeout so the UI
// never hangs. A recompile that forces a full reload is handled by mount restore.
const waitForRecompile = (onDone) => {
  let finished = false;
  let sawInvalid = false;
  let ws = null;
  const done = () => {
    if (finished) return;
    finished = true;
    clearTimeout(timer);
    try { if (ws) ws.close(); } catch (_) {}
    onDone();
  };
  try {
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    ws.onmessage = (evt) => {
      let msg;
      try { msg = JSON.parse(evt.data); } catch (_) { return; }
      const type = msg && msg.type;
      if (['invalid', 'static-changed', 'content-changed'].includes(type)) {
        sawInvalid = true;
      } else if (sawInvalid && ['ok', 'hash', 'errors'].includes(type)) {
        done(); // recompilation finished (with or without warnings/errors)
      }
    };
    ws.onerror = () => {}; // fall back to the timeout / reload-restore path
  } catch (_) {}
  const timer = setTimeout(done, 20000);
};

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

  // Per-module install config (admin / SMTP / Stripe)
  const [config, setConfig] = useState(EMPTY_CONFIG);
  const setConfigField = (group, key, value) =>
    setConfig((c) => ({ ...c, [group]: { ...c[group], [key]: value } }));

  // Install result
  const [result, setResult] = useState(null);

  // True while waiting for the dev server to finish rebuilding after an
  // install/uninstall, so the result is shown only once the frontend is ready.
  const [recompiling, setRecompiling] = useState(false);

  // Installed modules
  const [installed, setInstalled]           = useState([]);
  const [uninstalling, setUninstalling]     = useState(null);
  const [uninstallResult, setUninstallResult] = useState(null);

  // Upgrade flow (installed app with a newer remote generation)
  const [upgradePreview, setUpgradePreview] = useState(null);
  const [upgradeResult, setUpgradeResult]   = useState(null);

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

    // If a recompile-triggered full reload interrupted a pending install/uninstall,
    // the dev server only reloads after a successful compile — so the rebuild is
    // already done. Restore the stored result and show it.
    const pending = readPending();
    if (pending) {
      if (pending.kind === 'uninstall') {
        setUninstallResult(pending.data);
      } else if (pending.kind === 'upgrade') {
        setUpgradeResult(pending.data);
        setStep(STEPS.UPGRADE_RESULT);
      } else {
        setResult(pending.data);
        setStep(STEPS.INSTALL);
      }
    }

    InstallerService.getStatus()
      .then((data) => {
        const on = data?.enabled !== false;
        setEnabled(on);
        if (!on) return;
        fetchInstalled();
        InstallerService.getSession()
          .then((session) => {
            // Keep the restored result on screen — load apps without resetting
            // the step back to the selection list.
            if (session.connected) fetchApps(pending ? { keepStep: true } : {});
          })
          .catch(() => {});
      })
      // If the status check itself fails, fall back to enabled and let the
      // normal flow surface any backend error.
      .catch(() => setEnabled(true));
  }, [fetchInstalled]);

  // Connection to the Migratis instance is gone — return to the login form
  // (with a reconnect message) instead of leaving the user on a failed screen.
  const showLogin = () => {
    setApps([]);
    setSelectedApp(null);
    setResult(null);
    setStep(STEPS.CONNECT);
    setError('not-connected');
  };

  const fetchApps = (opts = {}) => {
    if (!opts.keepStep) setLoading(true);
    setError('');
    InstallerService.listApps()
      .then((data) => {
        if (isDisconnected(data)) {
          showLogin();
          return;
        }
        setApps(data.apps || []);
        if (!opts.keepStep) setStep(STEPS.SELECT);
      })
      .catch(() => setError('connection-failed'))
      .finally(() => { if (!opts.keepStep) setLoading(false); });
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

  // From the app list: collect config first when the app needs it, else install.
  const handleProceedToInstall = () => {
    if (!selectedApp) return;
    const groups = requiredGroups(selectedApp);
    setError('');
    if (groups.user || groups.subscription) {
      setConfig(EMPTY_CONFIG);
      setStep(STEPS.CONFIG);
    } else {
      handleInstall();
    }
  };

  // Build the payload sent to the installer, including only the groups the app needs.
  const buildConfigPayload = () => {
    const groups = requiredGroups(selectedApp);
    const payload = {};
    if (groups.user) {
      payload.admin = config.admin;
      payload.email = config.email;
    }
    if (groups.subscription) {
      payload.stripe = config.stripe;
    }
    return payload;
  };

  const handleInstall = (cfg = {}) => {
    if (!selectedApp) return;
    setLoading(true);
    setError('');
    InstallerService.install(selectedApp.id, cfg)
      .then((data) => {
        if (isDisconnected(data)) {
          showLogin();
          return;
        }
        const showResult = () => {
          setResult(data);
          setStep(STEPS.INSTALL);
          fetchInstalled();
        };
        if (IS_DEV && data?.frontend_ok) {
          // Dev server: files landed in the mounted frontend; wait for it to
          // finish rebuilding before revealing the result.
          persistPending({ kind: 'install', data });
          setRecompiling(true);
          waitForRecompile(() => { setRecompiling(false); showResult(); });
        } else {
          showResult();
        }
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
        if (IS_DEV && data?.frontend_ok) {
          // Dev server: the removed module's files were deleted from the mounted
          // frontend; wait for the rebuild before showing the result.
          persistPending({ kind: 'uninstall', data });
          setRecompiling(true);
          waitForRecompile(() => {
            setRecompiling(false);
            setUninstallResult(data);
            fetchInstalled();
          });
        } else {
          setUninstallResult(data);
          fetchInstalled();
        }
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        const msg = detail?.[0]?.uninstall?.[0] || detail?.[0]?.module?.[0] || 'uninstall-failed';
        setUninstallResult({ success: false, error: msg });
      })
      .finally(() => setUninstalling(null));
  };

  // Upgrade: fetch the dry-run preview (pending versions + destructive/lossy
  // changes with live row counts) and show the confirmation screen.
  const handleUpgradePreview = (app) => {
    if (!app) return;
    setSelectedApp(app);
    setLoading(true);
    setError('');
    InstallerService.upgradePreview(app.id)
      .then((data) => {
        if (isDisconnected(data)) {
          showLogin();
          return;
        }
        if (data?.detail) {
          setError(data.detail?.[0]?.upgrade?.[0] || data.detail?.[0]?.download?.[0] || 'upgrade-failed');
          return;
        }
        setUpgradePreview(data);
        setStep(STEPS.UPGRADE_PREVIEW);
      })
      .catch(() => setError('upgrade-failed'))
      .finally(() => setLoading(false));
  };

  // Upgrade: the user confirmed the previewed changes — apply them.
  const handleUpgrade = () => {
    if (!selectedApp) return;
    setLoading(true);
    setError('');
    InstallerService.upgrade(selectedApp.id, true)
      .then((data) => {
        if (isDisconnected(data)) {
          showLogin();
          return;
        }
        if (data?.detail) {
          setError(data.detail?.[0]?.upgrade?.[0] || data.detail?.[0]?.download?.[0] || 'upgrade-failed');
          return;
        }
        const showRes = () => {
          setUpgradeResult(data);
          setStep(STEPS.UPGRADE_RESULT);
          fetchInstalled();
        };
        if (IS_DEV && data?.frontend_ok) {
          // The rewritten module files trigger a dev-server rebuild — wait for
          // it before revealing the result (mirrors install/uninstall).
          persistPending({ kind: 'upgrade', data });
          setRecompiling(true);
          waitForRecompile(() => { setRecompiling(false); showRes(); });
        } else {
          showRes();
        }
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        setError(detail?.[0]?.upgrade?.[0] || detail?.[0]?.download?.[0] || 'upgrade-failed');
      })
      .finally(() => setLoading(false));
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

  // Waiting for the dev server to finish rebuilding after an install/uninstall.
  if (recompiling) {
    return (
      <div className="container mt-4" style={{ maxWidth: 720 }}>
        <h2 className="mb-4">{t('installer-title')}</h2>
        <div className="card p-4 text-center">
          <LoaderIndicator />
          <p className="mt-3 mb-1">{t('recompiling-frontend')}</p>
          <small className="text-muted">{t('recompiling-frontend-help')}</small>
        </div>
      </div>
    );
  }

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
              clearPending();
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
                const alreadyInstalled = app.installed || installed.includes(app.module);
                const upgradable = alreadyInstalled && app.upgrade_available;
                return (
                  <button
                    key={app.id}
                    type="button"
                    className={`list-group-item list-group-item-action${selectedApp?.id === app.id ? ' active' : ''}${alreadyInstalled ? (upgradable ? ' list-group-item-warning' : ' list-group-item-success') : ''}`}
                    onClick={() => (!alreadyInstalled || upgradable) && setSelectedApp(app)}
                    disabled={alreadyInstalled && !upgradable}
                  >
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <strong>{app.name}</strong>
                      </div>
                      <div>
                        {alreadyInstalled && (
                          <span className="badge bg-success">{t('installed-badge')}</span>
                        )}
                        {upgradable && (
                          <span className="badge bg-warning text-dark ms-1">
                            {t('upgrade-badge', {
                              from: app.installed_schema_version || 1,
                              to: app.generation,
                            })}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          <div className="d-flex gap-2">
            <button
              className="btn btn-primary"
              disabled={!selectedApp || selectedApp?.installed || installed.includes(selectedApp?.module)}
              onClick={handleProceedToInstall}
            >
              {t('install-selected')}
            </button>
            {selectedApp?.upgrade_available && (
              <button
                className="btn btn-warning"
                onClick={() => handleUpgradePreview(selectedApp)}
              >
                {t('upgrade-selected')}
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── Step 2b: Per-module configuration ────────────────────────────── */}
      {!uninstallResult && step === STEPS.CONFIG && selectedApp && (
        <div className="card p-4">
          <h5 className="mb-1">{t('config-title', { app: selectedApp.name })}</h5>
          <p className="text-muted small mb-3">{t('config-help')}</p>
          {error && <div className="alert alert-danger">{t(error)}</div>}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleInstall(buildConfigPayload());
            }}
          >
            {requiredGroups(selectedApp).user && (
              <>
                <h6 className="mt-2">{t('config-admin')}</h6>
                <div className="mb-3">
                  <label className="form-label">{t('admin-email')}</label>
                  <input
                    type="email"
                    className="form-control"
                    value={config.admin.email}
                    onChange={(e) => setConfigField('admin', 'email', e.target.value)}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">{t('admin-password')}</label>
                  <input
                    type="password"
                    className="form-control"
                    value={config.admin.password}
                    onChange={(e) => setConfigField('admin', 'password', e.target.value)}
                  />
                </div>

                <h6 className="mt-3">{t('config-email')}</h6>
                {[
                  ['EMAIL_HOST', 'smtp-host'],
                  ['EMAIL_HOST_USER', 'smtp-user'],
                  ['EMAIL_HOST_PASSWORD', 'smtp-password'],
                  ['EMAIL_SENDER', 'email-sender'],
                  ['EMAIL_MODERATOR', 'email-moderator'],
                ].map(([key, label]) => (
                  <div className="mb-3" key={key}>
                    <label className="form-label">{t(label)}</label>
                    <input
                      type={key === 'EMAIL_HOST_PASSWORD' ? 'password' : 'text'}
                      className="form-control"
                      value={config.email[key]}
                      onChange={(e) => setConfigField('email', key, e.target.value)}
                    />
                  </div>
                ))}
              </>
            )}

            {requiredGroups(selectedApp).subscription && (
              <>
                <h6 className="mt-3">{t('config-stripe')}</h6>
                {[
                  ['STRIPE_API_KEY', 'stripe-publishable'],
                  ['STRIPE_SECRET_KEY', 'stripe-secret'],
                  ['STRIPE_WEBHOOK_SECRET_KEY', 'stripe-webhook'],
                ].map(([key, label]) => (
                  <div className="mb-3" key={key}>
                    <label className="form-label">{t(label)}</label>
                    <input
                      type="text"
                      className="form-control"
                      value={config.stripe[key]}
                      onChange={(e) => setConfigField('stripe', key, e.target.value)}
                    />
                  </div>
                ))}
              </>
            )}

            <div className="d-flex gap-2 mt-2">
              <button type="submit" className="btn btn-primary">
                {t('install-selected')}
              </button>
              <button
                type="button"
                className="btn btn-outline-secondary"
                onClick={() => { setStep(STEPS.SELECT); setError(''); }}
              >
                {t('back')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── Upgrade: preview / confirmation ──────────────────────────────── */}
      {!uninstallResult && step === STEPS.UPGRADE_PREVIEW && upgradePreview && (
        <div className="card p-4">
          <h5 className="mb-1">{t('upgrade-title', { app: selectedApp?.name })}</h5>
          <p className="text-muted small mb-3">
            {t('upgrade-versions', {
              from: upgradePreview.installed_version,
              to: upgradePreview.target_version,
            })}
          </p>
          {error && <div className="alert alert-danger">{t(error)}</div>}
          {upgradePreview.legacy && (
            <div className="alert alert-warning">{t('upgrade-legacy-warning')}</div>
          )}
          {upgradePreview.changes.length === 0 ? (
            <div className="alert alert-info">{t('upgrade-no-schema-changes')}</div>
          ) : (
            <ul className="list-group mb-3">
              {upgradePreview.changes.map((c, i) => (
                <li
                  key={i}
                  className={`list-group-item d-flex justify-content-between align-items-center${
                    c.severity === 'destructive'
                      ? ' list-group-item-danger'
                      : c.severity === 'lossy' ? ' list-group-item-warning' : ''
                  }`}
                >
                  <span>
                    <code>{c.model}</code>
                    {c.name && c.op !== 'rename_model' && <>.<code>{c.name}</code></>}
                    {' — '}{t(`upgrade-op-${c.op}`)}
                    {c.op === 'rename_field' && c.old_name && ` (${c.old_name} → ${c.name})`}
                    {c.op === 'alter_field' && c.from && c.to && ` (${c.from} → ${c.to})`}
                  </span>
                  {c.rows != null && (
                    <span className="badge bg-secondary">
                      {t('upgrade-rows-affected', { count: c.rows })}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
          {upgradePreview.requires_confirmation && (
            <div className="alert alert-danger">{t('upgrade-destructive-warning')}</div>
          )}
          <p className="small text-muted">{t('upgrade-backup-notice')}</p>
          <div className="d-flex gap-2">
            <button className="btn btn-warning" onClick={handleUpgrade}>
              {t('upgrade-confirm')}
            </button>
            <button
              className="btn btn-outline-secondary"
              onClick={() => { setUpgradePreview(null); setError(''); setStep(STEPS.SELECT); }}
            >
              {t('back')}
            </button>
          </div>
        </div>
      )}

      {/* ── Upgrade: result ──────────────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.UPGRADE_RESULT && upgradeResult && (
        <div className="card p-4">
          <div className={`alert ${upgradeResult.success ? 'alert-success' : 'alert-danger'} mb-3`}>
            {upgradeResult.success
              ? t('upgrade-success', {
                  module: upgradeResult.module,
                  from: upgradeResult.from_version,
                  to: upgradeResult.to_version,
                })
              : <>
                  {t('upgrade-failed-msg')}{' '}
                  {upgradeResult.rolled_back
                    ? t('upgrade-rolled-back')
                    : t('upgrade-rollback-failed')}
                </>}
          </div>

          {upgradeResult.migrate_output && (
            <pre className="bg-light p-2 small" style={{ maxHeight: 150, overflow: 'auto' }}>
              {upgradeResult.migrate_output}
            </pre>
          )}

          {upgradeResult.backup_path && (
            <p className="small text-muted">
              {t('upgrade-backup-at')} <code>{upgradeResult.backup_path}</code>
            </p>
          )}

          {/* Seeds are skipped on upgrade so user-edited data survives; new
              translation keys arrive only when the seed command is re-run. */}
          {upgradeResult.success && (
            <div className="alert alert-info">
              {t('upgrade-translations-hint')}
              <pre className="mb-0 mt-2 small bg-white p-2 rounded">
                {upgradeResult.translations_command}
              </pre>
            </div>
          )}

          {upgradeResult.success && (upgradeResult.restart_required || !IS_DEV) && (
            <div className="alert alert-warning">
              <strong>{t('almost-done')}</strong>
              {upgradeResult.restart_required && (
                <>
                  {' '}{t('restart-to-load-module')}
                  <pre className={`${IS_DEV ? 'mb-0' : 'mb-2'} mt-2 small bg-white p-2 rounded`}>docker restart backend-base-api-1</pre>
                </>
              )}
              {!IS_DEV && (
                <>
                  {t('rebuild-static-assets')}
                  <pre className="mb-0 mt-2 small bg-white p-2 rounded">npm run build</pre>
                </>
              )}
            </div>
          )}

          <button
            className="btn btn-secondary"
            onClick={() => {
              clearPending();
              setUpgradeResult(null);
              setUpgradePreview(null);
              setSelectedApp(null);
              fetchApps();
            }}
          >
            {t('back')}
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

          {/* Manual steps left for the user. Each is shown only when its side
              actually needs it: the backend restart when the server doesn't
              autoreload (production), and `npm run build` when the frontend is a
              static bundle (production). In dev both auto-apply, so this is hidden. */}
          {(result.restart_required || !IS_DEV) && (
            <div className="alert alert-warning">
              <strong>{t('almost-done')}</strong>
              {result.restart_required && (
                <>
                  {' '}{t('restart-to-load-module')}
                  <pre className={`${IS_DEV ? 'mb-0' : 'mb-2'} mt-2 small bg-white p-2 rounded`}>docker restart backend-base-api-1</pre>
                </>
              )}
              {!IS_DEV && (
                <>
                  {t('rebuild-static-assets')}
                  <pre className="mb-0 mt-2 small bg-white p-2 rounded">npm run build</pre>
                </>
              )}
            </div>
          )}

          <button
            className="btn btn-secondary"
            onClick={() => {
              clearPending();
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
