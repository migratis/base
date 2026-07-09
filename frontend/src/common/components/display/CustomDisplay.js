import React, { useMemo } from 'react';
import { getVisibleInteractions } from '../interactionVisibility';
import { sanitizeHtml } from '../../fields/sanitizeHtml';

class CustomDisplayErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error) {
    // Lift the crash out of the boundary (GAP_ANALYSIS_agent_lane_poc6.md #1c/#2):
    // the parent un-suppresses the deterministic embedded child list so children
    // still have a home, and reports the failure so it is more than a console.warn.
    // Guarded to fire once per mounted error.
    if (!this._reported) {
      this._reported = true;
      if (typeof this.props.onError === 'function') {
        try { this.props.onError(error); } catch (_e) { /* telemetry must not throw */ }
      }
    }
  }

  render() {
    if (this.state.hasError) {
      const { fallback: Fallback, fallbackProps } = this.props;
      console.warn('[CustomDisplay] Component error, falling back:', this.state.error);
      return <Fallback {...fallbackProps} />;
    }
    return this.props.children;
  }
}

function compileDisplay(componentName, code) {
  try {
    // Normalize literal escape sequences the AI sometimes emits in JSON strings
    const src = code.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\r/g, '');
    // `sanitizeHtml` is injected into scope so AI code may safely render
    // sanitized rich text via dangerouslySetInnerHTML without an import.
    // eslint-disable-next-line no-new-func
    const factory = new Function('React', 'sanitizeHtml', `${src}; return ${componentName};`);
    return factory(React, sanitizeHtml);
  } catch (err) {
    console.warn(`[CustomDisplay] Failed to compile ${componentName}:`, err);
    return null;
  }
}

/**
 * CustomDisplay
 *
 * Renders an AI-generated React display component for entities with display_mode='custom_display'.
 * The component code lives in sandboxConfig._custom_components[custom_display.name].
 *
 * Receives all standard display props (records, entityConfig, relOptions, onEdit, onDelete, t)
 * plus any static props from custom_display.props_schema.
 * Falls back to TableDisplay when code is missing or fails to compile.
 */
const CustomDisplay = ({
  records,
  entityConfig,
  relOptions,
  onEdit,
  onDelete,
  t,
  viewAs,
  sandboxConfig,
  FallbackDisplay,
  onRenderFailed,
  ...rest
}) => {
  const customDisplayDef = entityConfig?.display_mode_options?.custom_display || {};
  const componentName    = customDisplayDef.name;
  const propsSchema      = customDisplayDef.props_schema || {};
  const code = sandboxConfig?._custom_components?.[componentName];

  const CompiledComponent = useMemo(() => {
    if (!componentName || !code) return null;
    return compileDisplay(componentName, code);
  }, [componentName, code]);

  // AI-generated displays call getVisibleInteractions(config?.interactions,
  // record?.data) without a viewerRole arg. Bind viewAs and the per-app
  // role-rank lookup here so Stage A + Stage B run without touching every
  // generated component.
  const boundGetVisibleInteractions = useMemo(
    () => (interactions, recordData, parentRecordData) =>
      getVisibleInteractions(interactions, recordData, parentRecordData, viewAs, rest?.getRoleRank),
    [viewAs, rest?.getRoleRank],
  );

  // canCreate(entityName): may the current viewer write (create) records of that
  // entity? Lets a custom display gate a create affordance it composes for ANOTHER
  // entity (e.g. a "Write a Review" button on the Recipe display) by the target's
  // min_write_role — app-28 showed that button to `public`, whom the backend then
  // blocked (GAP_ANALYSIS_agent_lane_poc9.md #6). Ranks come from the same
  // per-app getRoleRank the interaction gates use; when a rank is unknown we
  // degrade to "allow" (best-effort, mirroring the interaction Stage-A gate).
  const canCreate = useMemo(() => {
    const getRoleRank = rest?.getRoleRank;
    return (entityName) => {
      const minWrite = sandboxConfig?.entities?.[entityName]?.min_write_role || 'user';
      if (typeof getRoleRank !== 'function') return true;
      const viewerRank = getRoleRank((viewAs || '').trim());
      const floorRank  = getRoleRank(minWrite);
      if (viewerRank == null || floorRank == null) return true;
      return viewerRank >= floorRank;
    };
  }, [sandboxConfig, viewAs, rest?.getRoleRank]);

  const fallbackProps = { records, entityConfig, relOptions, onEdit, onDelete, t, ...rest };

  if (!code || !CompiledComponent) {
    if (FallbackDisplay) return <FallbackDisplay {...fallbackProps} />;
    return null;
  }

  return (
    <CustomDisplayErrorBoundary
      fallback={FallbackDisplay || (() => null)}
      fallbackProps={fallbackProps}
      onError={(error) => {
        if (typeof onRenderFailed === 'function') onRenderFailed(componentName, error);
      }}
    >
      <CompiledComponent
        records={records}
        entityConfig={entityConfig}
        relOptions={relOptions}
        onEdit={onEdit}
        onDelete={onDelete}
        t={t}
        getVisibleInteractions={boundGetVisibleInteractions}
        canCreate={canCreate}
        viewAs={viewAs}
        {...propsSchema}
        {...rest}
      />
    </CustomDisplayErrorBoundary>
  );
};

export default CustomDisplay;
