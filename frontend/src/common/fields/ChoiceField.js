import { useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { useFormContext } from "react-hook-form";

export default function ChoiceField ({
  id,
  name,
  type = "checkbox",
  option,
  label,
  help = null,
  required = false,
  validate = null,
  disabled = false,
  isVisible = true,
  serverError,
  dispatch = () => {},
}) {

  const { t } = useTranslation('form');
  const { setValue, watch, formState: { errors } } = useFormContext();

  const getNestedError = (errors, path) => {
    return path.split('.').reduce((acc, key) => acc?.[key], errors);
  };
  
  const error = getNestedError(errors, name) || serverError;
  const fieldValue = watch(name);

  useEffect(() => {
    if (!isVisible) {
      setValue(name, type === 'checkbox' ? false : '');
    }
  }, [isVisible, name, setValue, type]);

  const isChecked = type === 'checkbox' ? fieldValue === true : fieldValue === option;

  const handleChange = (e) => {
    if (type === 'checkbox') {
      setValue(name, e.target.checked);
    } else {
      setValue(name, e.target.value);
    }
    dispatch(type === 'checkbox' ? e.target.checked : e.target.value);
  };

  return (
    <div className={`form-check ${isVisible ? '' : 'd-none'}`}>
      <input
        id={id?id:name + "-" + option}
        type={type}
        value={option}
        checked={isChecked}
        onChange={handleChange}
        disabled={disabled}
        className={`form-check-input ${ error ? 'is-invalid' : '' }`}
        aria-label={typeof label === 'string' ? label : ''}
      />
      <label htmlFor={id?id:name + "-" + option} className={`form-check-label ${ error ? 'text-danger' : '' }`}>
        {label}
        {required?<span style={{ color: 'red' }}>&nbsp;*</span>:""}
        {help ? <small className="form-text text-muted">&nbsp;&nbsp;{help}</small> : null}
      </label>
      <small className="form-text text-danger d-block">
        { !error?.type && error }
        { error?.type === 'required' && t("empty-field") }
        { error?.type === "validate" && error.message }
      </small>
    </div>
  );
};
