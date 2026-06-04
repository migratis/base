import React, { useMemo } from 'react';
import { getVisibleInteractions } from '../interactionVisibility';

class CustomDisplayErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
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
    // eslint-disable-next-line no-new-func
    const factory = new Function('React', `${src}; return ${componentName};`);
    return factory(React);
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

  const fallbackProps = { records, entityConfig, relOptions, onEdit, onDelete, t, ...rest };

  if (!code || !CompiledComponent) {
    if (FallbackDisplay) return <FallbackDisplay {...fallbackProps} />;
    return null;
  }

  return (
    <CustomDisplayErrorBoundary fallback={FallbackDisplay || (() => null)} fallbackProps={fallbackProps}>
      <CompiledComponent
        records={records}
        entityConfig={entityConfig}
        relOptions={relOptions}
        onEdit={onEdit}
        onDelete={onDelete}
        t={t}
        getVisibleInteractions={boundGetVisibleInteractions}
        {...propsSchema}
        {...rest}
      />
    </CustomDisplayErrorBoundary>
  );
};

export default CustomDisplay;
