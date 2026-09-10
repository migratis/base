import { useEffect, useMemo } from "react";
import Select from 'react-select';
import makeAnimated from 'react-select/animated';
import { useTranslation } from 'react-i18next';
import { Controller, useFormContext } from "react-hook-form";

export default function SelectField ({
  options,
  name,
  label,
  isMulti = false,
  help = null,
  placeholder,
  isSearchable = false,
  disabled = false,
  required = false,
  isVisible = true,
  serverError = null,
  // A FIELD does not decide where the caret goes — the FORM does. react-select
  // focuses itself on mount when this is on, so a form carrying several selects
  // had several of them claiming focus; a burst of `setValue` (an external
  // lookup fires one per mapped field) then had them handing focus back and
  // forth through re-renders that never settled, and the tab froze with no
  // console error at all. Prod app 8, on the four selects of its Title form —
  // and `EntityForm` had already been passing `autoFocus={false}` to four of
  // its own, one workaround per caller. A caller that genuinely wants the caret
  // still asks for it.
  autoFocus = false,
  inputClass = "",
  dispatch = () => {},
  onMenuScrollToBottom = () => {},
  menuShouldScrollIntoView = true,
  onInputChange = () => {},
  menuListProps = {},
  maxMenuHeight = 250,
  menuPortalTarget = null,
  menuPosition = 'absolute',  
  isLoading = false,
  validate = null,
}) {

  const { t } = useTranslation('form');
  // Built ONCE. `makeAnimated()` mints new component TYPES on every call, so
  // calling it in the render body hands react-select a different `components`
  // identity each pass and forces it to unmount and remount its whole subtree.
  // On a form that re-renders on every setValue — an external-source lookup
  // fires fifteen — that is what turned a render error into a frozen tab.
  const animatedComponents = useMemo(() => makeAnimated(), []);
  const { control, setValue, formState: { errors } } = useFormContext();
  // `render_as: 'select'` is a display choice over whatever the column holds,
  // so nothing guarantees options were supplied: only an `enum` carries them
  // from its `Field.choices`. Prod app 8's `Title.language` is a plain string
  // rendered as a select with NO options, and the day an external lookup began
  // filling it, `options.find(...)` on `undefined` threw on every render —
  // inside a Controller, under a form re-rendering fifteen times, so it hung
  // the tab instead of surfacing. A renderer must tolerate what it is handed
  // (`TagsField`'s rule, one component over).
  const opts = Array.isArray(options) ? options : [];

  const getNestedError = (errors, path) => {
    return path.split('.').reduce((acc, key) => acc?.[key], errors);
  };

  const error = getNestedError(errors, name) || serverError;

  useEffect(() => {
    if (!isVisible) {
      setValue(name, null);
    }
  }, [isVisible]);// eslint-disable-line react-hooks/exhaustive-deps

  return  (
    <div className={isVisible ?inputClass + (label ? ' migratis-field' : 'migratis-field-no-label'):'d-none'}>
      
      { label &&
        <label className={error ? 'text-danger' : ''}>
          {label}
          {required?<span style={{ color: 'red' }}>&nbsp;*</span>:""}
        </label>
      }

      { help && 
        <small className="form-text text-muted">
          {help}                                  
        </small>
      }

      <Controller
        name={name}
        control={control}
        rules={{
          required: required,
          ...(validate && { validate: validate })
        }}
        render={({ field }) => (
          <Select
            {...field}
            name={name}
            placeholder={placeholder}
            components={animatedComponents}
            isMulti={isMulti}
            closeMenuOnSelect={!isMulti}
            onMenuScrollToBottom={onMenuScrollToBottom}
            menuShouldScrollIntoView={menuShouldScrollIntoView}
            menuListProps={menuListProps}
            maxMenuHeight={maxMenuHeight}
            menuPortalTarget={menuPortalTarget}
            menuPosition={menuPosition}
            onInputChange={onInputChange}
            options={opts}
            className={error ? 'migratis-is-invalid w-100' : 'w-100' }
            styles={{
              menu: provided => ({ ...provided, zIndex: 9999 })
            }}
            aria-label={label}
            isDisabled={disabled}
            isSearchable={isSearchable}
            autoFocus={autoFocus}
            isLoading={isLoading}
            value={isMulti
              ? (Array.isArray(field.value) ? field.value.map(v => opts.find(o => o.value === v) || v).filter(Boolean) : [])
              : (field.value ? opts.find(o => o.value === field.value) || field.value : null)
            }
            onChange={(selected) => {
              if (isMulti) {
                field.onChange(selected ? selected.map(o => o.value) : []);
              } else {
                field.onChange(selected);
              }
              // Same escape hatch as InputField/TextareaField: let the parent
              // react to the choice (revealing a dependent field, refetching
              // options…). Single selects hand over the option object, so a
              // consumer can read both `.value` and `.label`; multi selects
              // hand over the array, mirroring what goes into the form state.
              dispatch(isMulti ? (selected || []) : selected);
            }}
          />
        )}
      />

      <small className="form-text text-danger">
        { !error?.type && error }
        { error?.type === 'required' && t("empty-field") }   
        { error?.type === "validate" && error.message }                                   
      </small> 

    </div>      
  );
}
