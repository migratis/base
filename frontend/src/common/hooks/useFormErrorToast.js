import { useEffect, useRef } from "react";
import { toast } from "react-toastify";

/**
 * Fires a toast ONCE per submit attempt when the form has validation errors.
 */
export const useFormErrorToast = ({
  errors,
  submitCount,
  message,
}) => {
  const shownRef = useRef(false);

  useEffect(() => {
    if (
      submitCount > 0 &&
      Object.keys(errors || {}).length > 0 &&
      !shownRef.current
    ) {
      toast.error(message);
      shownRef.current = true;
    }
  }, [errors, submitCount, message]);

  /**
   * Call this at the beginning of onSubmit()
   * so the toast can fire again on next submit
   */
  const resetToast = () => {
    shownRef.current = false;
  };

  return { resetToast };
};
