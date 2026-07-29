// =============================================================================
// PageShell — the one page surface every route renders into.
//
// Before this existed each page rolled its own chrome: a bare
// `<header className="sticky-top"><div className="row">…<h2>` here, a
// `container mt-4` there, a form stretched edge-to-edge across the 1400px
// content area somewhere else. The result read as a set of unrelated screens.
//
// A page now declares *what* it is (title, description, actions, how wide its
// content wants to be) and the shell decides how that looks. Retheming the
// application means editing `_layout.scss` and `PageShell`, not thirty
// components.
//
//   <PageShell title={t('register')} width="form">
//     <UserForm … />
//   </PageShell>
//
// `width` picks the measure the content reads best at — `form` for a single
// column of fields, `content` for prose and tabs, `wide` for lists and card
// grids, `full` to opt out. `panel={false}` skips the white surface for
// content that already brings its own (card grids, tab strips).
// =============================================================================

const WIDTHS = ['form', 'content', 'wide', 'full'];

export const PagePanel = ({ title, actions, className = '', children }) => (
  <section className={`page-panel ${className}`.trim()}>
    {(title || actions) && (
      <div className="page-panel-head">
        {title && <h3 className="page-panel-title">{title}</h3>}
        {actions && <div className="page-panel-actions">{actions}</div>}
      </div>
    )}
    {children}
  </section>
);

export const PageShell = ({
  title,
  description,
  actions,
  width = 'content',
  panel = true,
  sticky = false,
  className = '',
  children,
}) => {
  const measure = WIDTHS.includes(width) ? width : 'content';

  return (
    <div className={`page-shell page-shell--${measure} ${className}`.trim()}>
      {(title || description || actions) && (
        <header className={`page-shell-head${sticky ? ' sticky-top' : ''}`}>
          <div className="page-shell-heading">
            {title && <h1 className="page-shell-title">{title}</h1>}
            {description && <p className="page-shell-subtitle">{description}</p>}
          </div>
          {actions && <div className="page-shell-actions">{actions}</div>}
        </header>
      )}
      {panel ? <PagePanel>{children}</PagePanel> : children}
    </div>
  );
};

export default PageShell;
