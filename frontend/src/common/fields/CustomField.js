import React, { useMemo } from 'react';
import { useFormContext } from 'react-hook-form';
import InputField from './InputField';

// ── ErrorBoundary ─────────────────────────────────────────────────────────────

class CustomFieldErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      const { fallbackProps } = this.props;
      console.warn('[CustomField] Component error, falling back to InputField:', this.state.error);
      return <InputField {...fallbackProps} />;
    }
    return this.props.children;
  }
}

// ── Component compiler ────────────────────────────────────────────────────────

/**
 * Compiles AI-generated plain-React code (no JSX, no imports) into a React
 * component constructor. The code must define a named function whose name
 * matches `componentName`. React is injected into scope.
 *
 * Returns the compiled constructor, or null on error.
 */
function compileComponent(componentName, code) {
  try {
    // eslint-disable-next-line no-new-func
    const factory = new Function('React', `${code}; return ${componentName};`);
    return factory(React);
  } catch (err) {
    console.warn(`[CustomField] Failed to compile ${componentName}:`, err);
    return null;
  }
}

// ── CustomField ───────────────────────────────────────────────────────────────

/**
 * CustomField
 *
 * Renders an AI-generated React component for fields with render_as='custom'.
 * The component code lives in config._custom_components[custom_component.name].
 *
 * Props:
 *   name              {string}   react-hook-form field name
 *   label             {string}
 *   required          {boolean}
 *   disabled          {boolean}
 *   help              {string}
 *   fieldConfig       {object}   the field's config entry (contains custom_component)
 *   sandboxConfig     {object}   the top-level sandbox config (contains _custom_components)
 */
const CustomField = ({
  name,
  label,
  required = false,
  disabled = false,
  help = null,
  fieldConfig = {},
  sandboxConfig = {},
  ...rest
}) => {
  const { watch, setValue } = useFormContext();
  const value = watch(name);

  const customComponentDef = fieldConfig?.custom_component || {};
  const componentName = customComponentDef.name;
  const propsSchema   = customComponentDef.props_schema || {};
  const fallbackRenderAs = customComponentDef.fallback_render_as || 'input';
  const code = sandboxConfig?._custom_components?.[componentName];

  // Compile once per component name + code pair
  const CompiledComponent = useMemo(() => {
    if (!componentName || !code) return null;
    return compileComponent(componentName, code);
  }, [componentName, code]);

  const fallbackProps = {
    name,
    label,
    required,
    disabled,
    help,
    type: fallbackRenderAs === 'number' ? 'number' : 'text',
    ...rest,
  };

  // No code available yet — use fallback silently
  if (!code || !CompiledComponent) {
    return <InputField {...fallbackProps} />;
  }

  const handleChange = (newValue) => {
    setValue(name, newValue, { shouldValidate: true, shouldDirty: true });
  };

  return (
    <CustomFieldErrorBoundary fallbackProps={fallbackProps}>
      <div className="migratis-field">
        <CompiledComponent
          name={name}
          label={label}
          value={value}
          onChange={handleChange}
          disabled={disabled}
          required={required}
          {...propsSchema}
          {...rest}
        />
        {help && <small className="form-text text-muted">{help}</small>}
      </div>
    </CustomFieldErrorBoundary>
  );
};

export default CustomField;
