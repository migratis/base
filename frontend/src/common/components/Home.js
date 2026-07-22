import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useShell } from '../shell/ShellContext';
import {
  IoCodeSlashOutline as CodeIcon,
  IoSparklesOutline as SparklesIcon,
  IoRocketOutline as RocketIcon,
  IoShieldCheckmarkOutline as ShieldIcon,
  IoGitNetworkOutline as NetworkIcon,
  IoGlobeOutline as GlobeIcon,
  IoBuildOutline as BuildIcon,
  IoLayersOutline as LayersIcon,
  IoCheckmarkCircleOutline as CheckIcon,
} from 'react-icons/io5';

const Home = () => {
  const { useAuth } = useShell();
  const { user } = useAuth();
  const { t } = useTranslation('home');

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section text-center text-white py-5">
        <div className="container">
          <h1 className="display-4 fw-bold mb-3">{t('hero-title', 'Build Apps with AI')}</h1>
          <p className="lead mb-4">{t('hero-subtitle', 'Design, prototype, and generate full-stack applications powered by AI')}</p>
          {!user && (
            <Link to="/register" className="btn btn-light btn-lg px-5">
              {t('get-started', 'Get Started')}
            </Link>
          )}
        </div>
      </section>

      {/* Chapter 1: AI-Powered Generation */}
      <section className="chapter-section py-5">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-md-6">
              <div className="chapter-icon">
                <SparklesIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch1-title', 'AI-Powered Schema Design')}</h2>
              <p className="lead">{t('ch1-desc', 'Describe your application in plain language and let our AI generate the complete data model with entities, fields, relationships, and validation rules.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch1-f1', 'Natural language application descriptions')}</li>
                <li><CheckIcon className="me-2" /> {t('ch1-f2', 'Automatic entity and field generation')}</li>
                <li><CheckIcon className="me-2" /> {t('ch1-f3', 'Smart relationship detection')}</li>
                <li><CheckIcon className="me-2" /> {t('ch1-f4', 'AI-guided validation rules')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Chapter 2: Interactive Sandbox */}
      <section className="chapter-section py-5 bg-light">
        <div className="container">
          <div className="row align-items-center flex-row-reverse">
            <div className="col-md-6">
              <div className="chapter-icon">
                <BuildIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch2-title', 'Interactive Sandbox Testing')}</h2>
              <p className="lead">{t('ch2-desc', 'Test your data model in a live sandbox environment before generating any code. Create, edit, and delete records to verify your schema works exactly as intended.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch2-f1', 'Real-time data model testing')}</li>
                <li><CheckIcon className="me-2" /> {t('ch2-f2', 'Search, filter, and sort records')}</li>
                <li><CheckIcon className="me-2" /> {t('ch2-f3', 'Multiple display modes (table, cards, kanban)')}</li>
                <li><CheckIcon className="me-2" /> {t('ch2-f4', 'AI-powered sandbox configuration')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Chapter 3: Code Generation */}
      <section className="chapter-section py-5">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-md-6">
              <div className="chapter-icon">
                <CodeIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch3-title', 'One-Click Code Generation')}</h2>
              <p className="lead">{t('ch3-desc', 'Generate production-ready Django backend and React frontend code from your validated schema. Everything you need to deploy your application.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch3-f1', 'Django models and APIs')}</li>
                <li><CheckIcon className="me-2" /> {t('ch3-f2', 'React components and forms')}</li>
                <li><CheckIcon className="me-2" /> {t('ch3-f3', 'Admin interface configuration')}</li>
                <li><CheckIcon className="me-2" /> {t('ch3-f4', 'Database migrations included')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Chapter 4: Public "base" Repository */}
      <section className="chapter-section py-5 bg-light">
        <div className="container">
          <div className="row align-items-center flex-row-reverse">
            <div className="col-md-6">
              <div className="chapter-icon">
                <NetworkIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch4-title', 'Public "base" Repository')}</h2>
              <p className="lead">{t('ch4-desc', 'Migratis provides a public GitHub repository called "base" from which you can install any application generated by the platform. Your apps are ready to deploy in minutes.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch4-f1', 'Pre-configured Django project structure')}</li>
                <li><CheckIcon className="me-2" /> {t('ch4-f2', 'Ready-to-install application modules')}</li>
                <li><CheckIcon className="me-2" /> {t('ch4-f3', 'One-command deployment setup')}</li>
                <li><CheckIcon className="me-2" /> {t('ch4-f4', 'Shared infrastructure and dependencies')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Chapter 5: Multi-Language Support */}
      <section className="chapter-section py-5">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-md-6">
              <div className="chapter-icon">
                <GlobeIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch5-title', 'Multi-Language Support')}</h2>
              <p className="lead">{t('ch5-desc', 'Build applications that support multiple languages out of the box. Our AI generates translations for all your entities and fields.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch5-f1', 'Built-in i18n support')}</li>
                <li><CheckIcon className="me-2" /> {t('ch5-f2', 'AI-generated translations')}</li>
                <li><CheckIcon className="me-2" /> {t('ch5-f3', '40+ languages supported')}</li>
                <li><CheckIcon className="me-2" /> {t('ch5-f4', 'Easy translation management')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Chapter 6: Ready-Made Modules */}
      <section className="chapter-section py-5 bg-light">
        <div className="container">
          <div className="row align-items-center flex-row-reverse">
            <div className="col-md-6">
              <div className="chapter-icon">
                <LayersIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch6-title', 'Ready-Made Modules')}</h2>
              <p className="lead">{t('ch6-desc', 'Accelerate development with pre-built modules for authentication, subscriptions, internationalization, support tickets, and cookie consent.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch6-f1', 'User authentication & profiles')}</li>
                <li><CheckIcon className="me-2" /> {t('ch6-f2', 'Stripe subscription billing')}</li>
                <li><CheckIcon className="me-2" /> {t('ch6-f3', 'GDPR cookie consent')}</li>
                <li><CheckIcon className="me-2" /> {t('ch6-f4', 'Customer support system')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Chapter 7: Security & Best Practices */}
      <section className="chapter-section py-5">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-md-6">
              <div className="chapter-icon">
                <ShieldIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch7-title', 'Security & Best Practices')}</h2>
              <p className="lead">{t('ch7-desc', 'Generated code follows Django and React best practices with proper security measures, validation, and error handling built-in.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch7-f1', 'CSRF and XSS protection')}</li>
                <li><CheckIcon className="me-2" /> {t('ch7-f2', 'Input validation included')}</li>
                <li><CheckIcon className="me-2" /> {t('ch7-f3', 'Role-based access control')}</li>
                <li><CheckIcon className="me-2" /> {t('ch7-f4', 'Clean, documented code')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Chapter 8: Workflow Automation */}
      <section className="chapter-section py-5 bg-light">
        <div className="container">
          <div className="row align-items-center flex-row-reverse">
            <div className="col-md-6">
              <div className="chapter-icon">
                <RocketIcon size={64} />
              </div>
              <h2 className="mb-3">{t('ch8-title', 'Workflow Automation')}</h2>
              <p className="lead">{t('ch8-desc', 'Define automated workflows that trigger actions based on events. Create, update, compute, and export data automatically with AI-guided logic.')}</p>
            </div>
            <div className="col-md-6">
              <ul className="feature-list list-unstyled">
                <li><CheckIcon className="me-2" /> {t('ch8-f1', 'Event-driven automation')}</li>
                <li><CheckIcon className="me-2" /> {t('ch8-f2', 'AI-assisted workflow design')}</li>
                <li><CheckIcon className="me-2" /> {t('ch8-f3', 'Visual workflow builder')}</li>
                <li><CheckIcon className="me-2" /> {t('ch8-f4', 'Scheduled and triggered actions')}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      {!user && (
        <section className="cta-section text-center py-5 text-white">
          <div className="container">
            <h2 className="mb-4">{t('cta-title', 'Ready to Build Your First App?')}</h2>
            <p className="lead mb-4">{t('cta-desc', 'Start designing your application with AI-powered tools today.')}</p>
            <Link to="/register" className="btn btn-light btn-lg px-5">
              {t('get-started', 'Get Started')}
            </Link>
          </div>
        </section>
      )}
    </div>
  );
};

export default Home;
