import { useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Controller, useFormContext } from "react-hook-form";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { 
  IoCalendarOutline as CalendarOutline
} from 'react-icons/io5';

// react-datepicker formats whatever `selected` holds with date-fns, and date-fns
// throws `RangeError: Invalid time value` on anything it cannot parse. That throw
// happens during render, so it escapes to the top of the tree and blanks the whole
// page rather than spoiling one field. A sandbox config wrote the literal token
// `first_saturday_july` into a date default and took app 2's sandbox down for its
// main role. The picker's own contract is a Date or nothing, so coerce here:
// callers keep passing ISO strings (the shape every stored record uses) and
// anything unparseable degrades to an empty picker.
const toSelectedDate = (value) => {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  if (typeof value !== 'string' || !value.trim()) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

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
              selected={toSelectedDate(field.value)}
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
