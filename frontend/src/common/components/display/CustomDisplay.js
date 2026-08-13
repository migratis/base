import React, { useMemo } from 'react';
import { getVisibleInteractions } from '../interactionVisibility';
import { sanitizeHtml } from '../../fields/sanitizeHtml';
import MapView from '../../fields/MapView';
import { exportData } from '../../tools/export';

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

// Un-double-escape a body that survived one JSON encoding too many — the whole
// component on ONE line, its newlines still the two characters `\` `n`.
// A body that already has real newlines is real source, and every `\n` left in
// it is the CODE's own escape: rewriting those turns `join('\n')` into a quote,
// a line break and a quote, which no JS engine accepts ("string literal
// contains an unescaped line break" — prod app 3's A3_StageMapDisplay, refused
// by the very step meant to rescue it). Mirrors the backend's
// `component_code.normalise_component_code`, so a component is linted and
// compiled from the same source.
function normalizeComponentCode(code) {
  if (/\n/.test(code)) return code;
  return code.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\r/g, '');
}

function compileDisplay(componentName, code) {
  try {
    const src = normalizeComponentCode(code);
    // `sanitizeHtml` is injected into scope so AI code may safely render
    // sanitized rich text via dangerouslySetInnerHTML without an import.
    // `MapView` is injected for the same reason one level up: an entity with a
    // geo field is routed to a custom_display by the blocking hub rule, and a
    // custom_display has no imports and no Leaflet global — so without this
    // reference there is no way for generated code to draw a map at all. App 2
    // hand-rolled `L.map(...)` behind a `typeof L` guard and drew nothing,
    // forever, while promising an interactive OpenStreetMap.
    // "use strict" (§7a) makes an implicit-global assignment inside the component
    // (e.g. `img = r.data.image`) throw here — the same class ESLint no-undef
    // rejects at CRA build time — instead of silently creating a global, closing
    // the sandbox-vs-installed-app fidelity gap.
    // eslint-disable-next-line no-new-func
    // `exportData` is the fourth injected name, and the only one that writes
    // anything: it takes rows the component already has and hands the browser
    // a file. It reaches no network — the compile scope never gets one — so a
    // component can offer an export without being able to send anything
    // anywhere.
    const factory = new Function(
      'React', 'sanitizeHtml', 'MapView', 'exportData',
      `"use strict";\n${src}; return ${componentName};`,
    );
    return factory(React, sanitizeHtml, MapView, exportData);
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
