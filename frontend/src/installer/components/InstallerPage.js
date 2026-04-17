import { useState, useEffect, useCallback } from 'react';
import InstallerService from '../services/installer.service';
import { LoaderIndicator } from '../../common/components/LoaderIndicator';

const STEPS = { CONNECT: 'connect', SELECT: 'select', INSTALL: 'install' };

const InstallerPage = () => {
  const [step, setStep]       = useState(STEPS.CONNECT);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  // Connect form
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [url, setUrl]           = useState('');

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

  // Check existing session on mount
  useEffect(() => {
    fetchInstalled();
    InstallerService.getSession()
      .then((data) => {
        if (data.connected) fetchApps();
      })
      .catch(() => {});
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
      .then(() => fetchApps())
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
    if (!window.confirm(`Uninstall "${module}"?\n\nThis will revert all migrations and remove all files for this module.`)) return;
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

  if (loading) return <LoaderIndicator />;

  return (
    <div className="container mt-4" style={{ maxWidth: 720 }}>
      <h2 className="mb-4">Installer</h2>

      {/* ── Uninstall result ─────────────────────────────────────────────── */}
      {uninstallResult && (
        <div className="card p-4 mb-4">
          <h5 className="mb-3">Uninstall result</h5>
          <div className={`alert ${uninstallResult.success ? 'alert-success' : 'alert-danger'} mb-3`}>
            {uninstallResult.success
              ? <>
                  Module <strong>{uninstallResult.module}</strong> uninstalled successfully.
                  {uninstallResult.migrate_ok
                    ? ' Migrations reverted.'
                    : ' Warning: migration revert failed — check output below.'}
                  {!uninstallResult.migrate_ok && uninstallResult.migrate_output && (
                    <pre className="bg-light p-2 mt-2 small mb-0" style={{ maxHeight: 120, overflow: 'auto' }}>
                      {uninstallResult.migrate_output}
                    </pre>
                  )}
                  {uninstallResult.restart_required && (
                    <div className="mt-2 small">
                      Restart the backend container to complete the removal:
                      <pre className="mb-0 mt-1 bg-white p-2 rounded">docker restart backend-base-api-1</pre>
                    </div>
                  )}
                </>
              : `Error: ${uninstallResult.error}`}
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
            Back
          </button>
        </div>
      )}

      {/* ── Installed modules ────────────────────────────────────────────── */}
      {installed.length > 0 && (
        <div className="card p-4 mb-4">
          <h5 className="mb-3">Installed modules</h5>
          <ul className="list-group">
            {installed.map((mod) => (
              <li key={mod} className="list-group-item d-flex justify-content-between align-items-center">
                <code>{mod}</code>
                <button
                  className="btn btn-sm btn-outline-danger"
                  disabled={uninstalling === mod}
                  onClick={() => handleUninstall(mod)}
                >
                  {uninstalling === mod ? 'Uninstalling…' : 'Uninstall'}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Step 1: Connect ──────────────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.CONNECT && (
        <div className="card p-4">
          <h5 className="mb-3">Connect to Migratis</h5>
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleConnect}>
            <div className="mb-3">
              <label className="form-label">Email</label>
              <input
                type="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Password</label>
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
                Migratis URL{' '}
                <small className="text-muted">(leave blank for default)</small>
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
              Connect
            </button>
          </form>
        </div>
      )}

      {/* ── Step 2: Select app ───────────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.SELECT && (
        <div className="card p-4">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="mb-0">Select an application to install</h5>
            <button className="btn btn-sm btn-outline-secondary" onClick={handleDisconnect}>
              Disconnect
            </button>
          </div>
          {error && <div className="alert alert-danger">{error}</div>}
          {apps.length === 0 ? (
            <div className="alert alert-info">No generated applications found.</div>
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
                        <span className="ms-2 text-muted small">module: {app.module}</span>
                      </div>
                      {alreadyInstalled && (
                        <span className="badge bg-success">Installed</span>
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
            Install selected app
          </button>
        </div>
      )}

      {/* ── Step 3: Result ───────────────────────────────────────────────── */}
      {!uninstallResult && step === STEPS.INSTALL && result && (
        <div className="card p-4">
          <div className={`alert ${result.success ? 'alert-success' : 'alert-danger'} mb-3`}>
            {result.success
              ? `Module "${result.module}" installed successfully.`
              : 'Installation failed.'}
          </div>

          <div className="mb-3">
            <strong>Backend migration:</strong>{' '}
            {result.migrate_deferred
              ? <span className="text-info">Applied automatically on restart</span>
              : <span className={result.migrate_ok ? 'text-success' : 'text-danger'}>{result.migrate_ok ? 'OK' : 'Failed'}</span>
            }
            {!result.migrate_deferred && result.migrate_output && (
              <pre className="bg-light p-2 mt-1 small" style={{ maxHeight: 150, overflow: 'auto' }}>
                {result.migrate_output}
              </pre>
            )}
          </div>

          <div className="mb-3">
            <strong>Seed translations:</strong>{' '}
            {result.migrate_deferred
              ? <span className="text-info">Applied automatically on restart</span>
              : <span className={result.seed_ok ? 'text-success' : 'text-danger'}>{result.seed_ok ? 'OK' : 'Failed'}</span>
            }
            {!result.migrate_deferred && result.seed_output && (
              <pre className="bg-light p-2 mt-1 small" style={{ maxHeight: 100, overflow: 'auto' }}>
                {result.seed_output}
              </pre>
            )}
          </div>

          <div className="mb-3">
            <strong>Frontend files:</strong>{' '}
            <span className={result.frontend_ok ? 'text-success' : 'text-warning'}>
              {result.frontend_ok ? 'Installed automatically' : 'Not applied (volume not mounted)'}
            </span>
          </div>

          {result.restart_required && (
            <div className="alert alert-warning">
              <strong>Almost done!</strong> Restart the backend container to load the new module:
              <pre className="mb-2 mt-2 small bg-white p-2 rounded">docker restart backend-base-api-1</pre>
              If your frontend is served by nginx, also rebuild the static assets:
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
            Install another
          </button>
        </div>
      )}
    </div>
  );
};

export default InstallerPage;
