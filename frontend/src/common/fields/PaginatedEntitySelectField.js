import { useState, useEffect, useMemo } from "react";
import SelectField from "./SelectField";
import CommonService from "../services/common.service";
import { ITEMS_PER_PAGE as pageSize } from "../../settings";
import { useTranslation } from 'react-i18next';
import { IoAddCircleOutline as AddCircleOutline } from 'react-icons/io5';
import { useNavigate } from "react-router-dom";
import { COLOR_LINK } from "../../settings";

export default function PaginatedEntitySelectField ({
  app,
  entity,
  noAddInvite = false,
  status = null,
  valueField = "id",
  labelField = "name",
  name,
  label,
  isMulti = false,
  help = null,
  placeholder = "",
  isSearchable = false,
  required = false,
  isVisible = true,
  serverError = null,
  autoFocus = true,
  inputClass = "",
  disabled = false,
  dispatch = () => {},
}) {
  const { t } = useTranslation(entity);
  const navigate = useNavigate();
  const [options, setOptions] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentTerm, setCurrentTerm] = useState("");
  
  const fetchEntities = async (page, search) => {
    setLoading(true);
    const data = await CommonService.getEntities(app, entity, status, search, page);
    const list = data?.items ?? [];
    const count = data?.count ?? 0;
    const newOptions = list.map((item) => ({
      value: item[valueField],
      label: item[labelField],
      raw: item,
    }));
    setHasMore((page - 1) * pageSize < count);

    if (search !== "") setOptions(newOptions)
    else setOptions((prev) => {
      const existingIds = new Set(newOptions.map(o => o.value));
      const preserveSelected = prev.filter(v => !existingIds.has(v.value));
      return [...preserveSelected, ...newOptions];
    });

    setLoading(false);
  };
  
  const debounceSearch = (func, wait) => {
    let timeout = null;
    return function executedFunction(...args) {
      const later = () => {
        timeout = null;
        func(...args);
      };
      if (timeout) clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };

  const handleInputChange = (term) => {    
    setCurrentPage(1);
    setCurrentTerm(term);   
    fetchEntities(1, term);
  };
  
  const debouncedInputChange = useMemo(() => {
    debounceSearch(handleInputChange, 350);// eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleMenuScrollToBottom = () => { 
    if (loading || !hasMore) return; 
    setCurrentPage(currentPage + 1);
    fetchEntities(currentPage + 1, currentTerm);  
  }; 

  useEffect(() => { 
    fetchEntities(1, ""); 
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <SelectField
        name={name}
        help={help}
        required={required}
        isVisible={isVisible}
        autoFocus={autoFocus}
        dispatch={dispatch}
        serverError={serverError}
        label={label}
        placeholder={placeholder}
        disabled={disabled}
        isSearchable={isSearchable}
        options={options}
        isMulti={isMulti}
        inputClass={inputClass}
        onInputChange={debouncedInputChange}
        onMenuScrollToBottom={handleMenuScrollToBottom}
        menuShouldScrollIntoView={false}
        isLoading={loading}
      />

      { !noAddInvite && !loading && options.length === 0 && currentTerm === "" &&
        <div className="migratis-field">
          {t(`no-${entity}-yet-add-first`)}
          <span className="link action" onClick={() => navigate(`/${app}/${entity}s?add=1`)}>
            <AddCircleOutline color={COLOR_LINK} title={t(`add-${entity}`)} height="30px" width="30px"/>
          </span>
        </div>
      }
    </>
  );
}