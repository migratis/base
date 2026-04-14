import { Link } from 'react-router-dom';

const Step = ({ number, title, children }) => (
  <div className="d-flex gap-3 mb-4">
    <div
      className="flex-shrink-0 d-flex align-items-center justify-content-center rounded-circle fw-bold text-white"
      style={{ width: 36, height: 36, minWidth: 36, background: 'var(--color-primary, #d97757)' }}
    >
      {number}
    </div>
    <div>
      <h5 className="mb-1">{title}</h5>
      <div className="text-muted">{children}</div>
    </div>
  </div>
);

const Home = () => (
  <div className="container py-5" style={{ maxWidth: 740 }}>

    <div className="text-center mb-5">
      <h1 className="fw-bold mb-2">Get Started with Migratis</h1>
      <p className="lead text-muted">
        Generate a full-stack application in minutes — no code required.
      </p>
    </div>

    <div className="card shadow-sm p-4 mb-4">
      <Step number={1} title="Generate your application on migratis.ai">
        <p className="mb-2">
          Go to{' '}
          <a href="https://migratis.ai" target="_blank" rel="noreferrer">
            migratis.ai
          </a>{' '}
          and describe your application in plain language. The AI will build the
          full data model (entities, fields, relationships) and a live sandbox
          preview you can tweak until it matches what you need.
        </p>
        <p className="mb-0">
          Once you are happy with the result, click <strong>Generate</strong> to
          produce the deployable package.
        </p>
      </Step>

      <Step number={2} title="Run this base environment with Docker">
        <p className="mb-1">Clone the base repository and start the containers:</p>
        <pre className="bg-light rounded p-3 small mb-2">{`git clone https://github.com/migratis/base.git
cd base/backend && bash build-docker-local.sh
cd ../frontend && docker compose up -d`}</pre>
        <p className="mb-0">
          The backend runs on{' '}
          <code>http://127.0.0.1:8004</code> and the frontend on{' '}
          <code>http://127.0.0.1:3002</code>. No database setup needed — SQLite
          is used by default.
        </p>
      </Step>

      <Step number={3} title="Install your application with the Installer">
        <p className="mb-2">
          Open the{' '}
          <Link to="/installer">
            <strong>Installer</strong>
          </Link>{' '}
          page (or click the download icon in the sidebar) and connect with your
          migratis.ai credentials. Select the generated application and click{' '}
          <strong>Install</strong>.
        </p>
        <p className="mb-0">
          The installer will automatically:
        </p>
        <ul className="mt-1 mb-0">
          <li>Download and extract the backend Django module</li>
          <li>Activate the required framework modules in settings</li>
          <li>Run database migrations</li>
          <li>Seed translation strings</li>
        </ul>
      </Step>

      <Step number={4} title="Restart the backend">
        <p className="mb-1">Restart the backend container to load the new module:</p>
        <pre className="bg-light rounded p-3 small mb-2">{`docker restart backend-base-api-1`}</pre>
        <p className="mb-1">
          <strong>If your frontend is served by nginx</strong> (production build),
          rebuild the static assets from inside the <code>frontend/</code> directory:
        </p>
        <pre className="bg-light rounded p-3 small mb-0">{`npm run build`}</pre>
      </Step>

      <Step number={5} title="Create your first admin user">
        <pre className="bg-light rounded p-3 small mb-0">{`docker exec -it backend-base-api-1 bash
python /backend/manage.py createsuperuser`}</pre>
      </Step>
    </div>

    <div className="card border-0 bg-light p-4">
      <h6 className="fw-semibold mb-2">Useful links</h6>
      <ul className="mb-0 small">
        <li><a href="https://migratis.ai" target="_blank" rel="noreferrer">migratis.ai</a> — application generator</li>
        <li><a href="https://github.com/migratis/base" target="_blank" rel="noreferrer">github.com/migratis/base</a> — this base environment</li>
        <li><Link to="/installer">Installer</Link> — connect, browse and install generated apps</li>
      </ul>
    </div>

  </div>
);

export default Home;
