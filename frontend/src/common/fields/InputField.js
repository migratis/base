import { useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useFormContext } from "react-hook-form";
import { 
  IoCloseCircle as CloseCircle,
  IoHelpCircleOutline as HelpCircleOutline 
} from 'react-icons/io5';
import { COLOR_LINK } from '../../settings';

export default function InputField ({
  name,
  label,
  type = "text",
  help = null,
  iconHelp = false,
  iconReset = false,    
  required = false,
  maxLength = 500,
  pattern = null,
  validate = null,
  placeholder = "",
  disabled = false,
  isVisible = true,
  serverError = null,
  inputClass = "",
  dispatch = () => {},
}) {

  const { t } = useTranslation('form');
  const { register, setValue, watch, formState: { errors } } = useFormContext();
  const currentValue = watch(name);

  const getNestedError = (errors, path) => {
    return path.split('.').reduce((acc, key) => acc?.[key], errors);
  };

  const error = getNestedError(errors, name) || serverError;

  const validateRef = useRef(validate);
  useEffect(() => { validateRef.current = validate; }, [validate]);

  const registering = register(name, {
    required: required,
    maxLength: maxLength,
    ...(type === "number" && {
      setValueAs: v => {
        if (v === "" || v === null || v === undefined) return "";
        const parsed = parseFloat(String(v).replace(/ /g, "").replace(/,/g, "."));
        return isNaN(parsed) ? v : parsed;
      }
    }),
    validate: (value) => {
      // 1. Built-in numeric pattern check
      if (!pattern && type === "number" && value !== "") {
        const decimalPattern = /^\d*(?:[.,]\d{0,2})?$/;
        const raw = String(value).replace(/ /g, "");
        if (!decimalPattern.test(raw.replace(".", ","))) {
          return t('Input should be a valid decimal');
        }
      }
      // 2. External pattern check
      if (pattern && value !== "") {
        const regex = pattern.value instanceof RegExp ? pattern.value : new RegExp(pattern.value);
        if (!regex.test(value)) {
          return pattern.message || t('value is not valid');
        }
      }
      // 3. External validate prop (via ref to avoid stale closure)
      if (validateRef.current) {
        return validateRef.current(value);
      }
      return true;
    },
  });

  const handleReset = () => {
    setValue(name, "");
  };

  useEffect(() => {
    if (!isVisible) {
      setValue(name, "");
    }
  }, [isVisible, name, setValue]);

  return (

    <div className={isVisible ?'migratis-field':'d-none'}>
      { label &&
        <label className={error ? 'text-danger' : ''}>
          {label}
          {label && required?<span style={{ color: 'red' }}>&nbsp;*</span>:""}
        </label>
      }
      { help &&
        <small className="form-text text-muted">
          {help}                                  
        </small>
      }
  
      <input {...registering}
        name={name}
        type={type === 'number' ? 'text' : type}
        disabled={disabled}
        placeholder={placeholder}
        className={inputClass + `form-control ${ error ? 'is-invalid' : '' }`}
        aria-label={label}
        lang="en-US"
        {...((type === "number") && { inputMode: "decimal" })}
        onChange={ (e) => {
          registering.onChange(e);
          dispatch(e.target.value);
        }}            
      />

      <span className="input-icon">
        { iconReset && currentValue !== "" &&
          <CloseCircle 
            color="#000000" 
            title={t('reset')} 
            onClick={handleReset}
          />
        }
        { iconHelp &&
          <HelpCircleOutline
            color={COLOR_LINK} 
            title={iconHelp} 
          />
        } 
      </span>     
      { error &&
        <small className="form-text text-danger">
          { !error?.type && error }
          { error?.type === 'required' && t("empty-field") }
          { error?.type === "maxLength" && t("max-length-exceeded") } 
          { error?.type === "validate" && error.message }                                            
        </small> 
      }
    </div>
  );
}
