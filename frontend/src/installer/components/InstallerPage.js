import { useState, useEffect } from 'react';
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
  const [apps, setApps]           = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);

  // Install result
  const [result, setResult] = useState(null);

  // Check existing session on mount
  useEffect(() => {
    InstallerService.getSession()
      .then((data) => {
        if (data.connected) fetchApps();
      })
      .catch(() => {});
  }, []);

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
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        const msg = detail?.[0]?.install?.[0] || detail?.[0]?.download?.[0] || 'install-failed';
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  if (loading) return <LoaderIndicator />;

  return (
    <div className="container mt-4" style={{ maxWidth: 720 }}>
      <h2 className="mb-4">Installer</h2>

      {/* ── Step 1: Connect ──────────────────────────────────────────────── */}
      {step === STEPS.CONNECT && (
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
      {step === STEPS.SELECT && (
        <div>
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
              {apps.map((app) => (
                <button
                  key={app.id}
                  type="button"
                  className={`list-group-item list-group-item-action${selectedApp?.id === app.id ? ' active' : ''}`}
                  onClick={() => setSelectedApp(app)}
                >
                  <strong>{app.name}</strong>
                  <span className="ms-2 text-muted small">module: {app.module}</span>
                </button>
              ))}
            </div>
          )}
          <button
            className="btn btn-primary"
            disabled={!selectedApp}
            onClick={handleInstall}
          >
            Install selected app
          </button>
        </div>
      )}

      {/* ── Step 3: Result ───────────────────────────────────────────────── */}
      {step === STEPS.INSTALL && result && (
        <div>
          <div className={`alert ${result.success ? 'alert-success' : 'alert-danger'} mb-3`}>
            {result.success
              ? `Module "${result.module}" installed successfully.`
              : 'Installation failed.'}
          </div>

          <div className="mb-3">
            <strong>Backend migration:</strong>{' '}
            <span className={result.migrate_ok ? 'text-success' : 'text-danger'}>
              {result.migrate_ok ? 'OK' : 'Failed'}
            </span>
            {result.migrate_output && (
              <pre className="bg-light p-2 mt-1 small" style={{ maxHeight: 150, overflow: 'auto' }}>
                {result.migrate_output}
              </pre>
            )}
          </div>

          <div className="mb-3">
            <strong>Seed translations:</strong>{' '}
            <span className={result.seed_ok ? 'text-success' : 'text-danger'}>
              {result.seed_ok ? 'OK' : 'Failed'}
            </span>
            {result.seed_output && (
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
