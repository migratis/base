import { useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { useFormContext } from "react-hook-form";

export default function TextareaField ({
  name,
  label,
  help = null,
  required = false,
  maxLength=5000,
  pattern = null,
  validate = null,
  placeholder,
  disabled,
  cols = null,
  rows = 1,
  isVisible = true,
  serverError = false,
  inputClass = "",
  dispatch = () => {}
}) {

  const { t } = useTranslation('form');
  const { register, setValue, formState: { errors } } = useFormContext();

  const getNestedError = (errors, path) => {
    return path.split('.').reduce((acc, key) => acc?.[key], errors);
  };

  const error = getNestedError(errors, name) || serverError;
  const registering = register(name, {
    shouldUnregister: true,
    required: required,
    maxLength: maxLength,
    ...(pattern && { pattern: pattern }),
    ...(validate && { validate: validate }),
  });

  useEffect(() => {
    if (!isVisible) {
      setValue(name, null);
    }
  }, [isVisible, name, setValue]);

  return (
    <div className={isVisible ?'migratis-field':'d-none'}>

      <label className={error ? 'text-danger' : ''}>
        {label}
        {required?<span style={{ color: 'red' }}>&nbsp;*</span>:""}
      </label>
      
      { help &&
        <small className="form-text text-muted">
          {help}                                  
        </small>
      }

      <textarea {...registering}
        name={name}
        cols={cols}
        rows={rows}
        onChange={(e) => {
            registering.onChange(e);          
            dispatch(e.target.value);
        }}
        disabled={disabled}
        placeholder={placeholder}
        className={inputClass + `form-control ${ error ? 'is-invalid' : '' }`}
        aria-label={label}
        lang="en-US"
      />

      <small className="form-text text-danger">
        { !error?.type && error }
        { error?.type === 'required' && t("empty-field") }
        { error?.type === "maxLength" && t("max-length-exceeded") }  
        { error?.type === "pattern" && error.message }          
        { error?.type === "validate" && error.message }                                              
      </small> 
      
    </div>
  );
}
