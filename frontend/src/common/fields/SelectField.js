import { useEffect } from "react";
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
  autoFocus = true,
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
  const animatedComponents = makeAnimated();
  const { control, setValue, formState: { errors } } = useFormContext();

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
            options={options}
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
              ? (Array.isArray(field.value) ? field.value.map(v => options.find(o => o.value === v) || v).filter(Boolean) : [])
              : (field.value ? options.find(o => o.value === field.value) || field.value : null)
            }
            onChange={(selected) => {
              if (isMulti) {
                field.onChange(selected ? selected.map(o => o.value) : []);
              } else {
                field.onChange(selected ? selected.value : null);
              }
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
