import { useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Controller, useFormContext } from "react-hook-form";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { 
  IoCalendarOutline as CalendarOutline
} from 'react-icons/io5';

export default function DateField({
  name,
  label,
  minDate,
  maxDate,
  showMonthDropdown = true,
  showYearDropdown = true,
  dropdownMode = 'select',
  dateFormat = "dd-MM-yyyy",
  required = false,
  placeholder = "",
  isVisible = true,
  serverError = null,
  className = "",
  disabled = false,
  dispatch = () => {},
}) {

  const { t } = useTranslation('form');
  const { control, setValue, formState: { errors } } = useFormContext();
  const dateRef = useRef(null);
  const error = errors?.[name] || serverError;

  const handleOpenDatePicker = () => {
    dateRef.current?.setOpen(true);
  };

  useEffect(() => {
    if (!isVisible) {
      setValue(name, null);
    }
  }, [isVisible, name, setValue]);

  return (
    <div className={isVisible ?'migratis-field':'d-none'}>
      {label && (
        <label htmlFor={name} className={error ? "text-danger" : ""}>
          {label}
          {required && <span style={{ color: "red" }}> *</span>}
        </label>
      )}

      <div className="datepicker-wrapper">
        <Controller
          name={name}
          control={control}
          rules={required && { required: true }}
          onChange={(e) => {
            dispatch(e.target.value);
          }}
          render={({ field }) => (
            <DatePicker
              ref={dateRef}
              selected={field.value}
              onChange={field.onChange}
              minDate={minDate}
              maxDate={maxDate}
              dateFormat={dateFormat}
              disabled={disabled}
              placeholderText={placeholder}
              className={`form-control ${(error || serverError) ? "is-invalid" : ""} ${className}`}
              showMonthDropdown={showMonthDropdown}
              showYearDropdown={showYearDropdown}
              dropdownMode={dropdownMode}
            />
          )}
        />
        <span className="input-icon">
            <CalendarOutline
                color={'#000000'} 
                title={t('select-date')} 
                onClick={handleOpenDatePicker} 
            />
        </span>
      </div>

      {error && (
        <small className="form-text text-danger">
            { !error && serverError }    
            { error.type === 'required' && t('empty-field') }
        </small>
      )}
    </div>
  );
}
