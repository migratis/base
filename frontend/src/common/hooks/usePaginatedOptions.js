import { useState, useEffect, useCallback, useMemo } from 'react';
import CommonService from '../services/common.service';
import { ITEMS_PER_PAGE as pageSize } from '../../settings';

/**
 * usePaginatedOptions
 *
 * Standalone hook that fetches paginated entity options for a plain react-select.
 * Mirrors the fetch logic of PaginatedEntitySelectField but without any form context.
 *
 * @param {string}  app          Django app name (e.g. 'generator')
 * @param {string}  entity       Entity name (e.g. 'application', 'entity')
 * @param {string}  status       Filter by status ('active' | 'inactive' | null)
 * @param {object}  extraParams  Extra query params (e.g. { application: 5 })
 * @param {boolean} enabled      Set to false to skip fetching (e.g. when a parent isn't selected yet)
 *
 * @returns {{
 *   options:               Array,    react-select option objects { value, label }
 *   isLoading:             boolean,
 *   onInputChange:         Function, pass to react-select onInputChange
 *   onMenuScrollToBottom:  Function, pass to react-select onMenuScrollToBottom
 *   reset:                 Function, clears options and resets pagination
 * }}
 */
export default function usePaginatedOptions({
  app,
  entity,
  status = null,
  extraParams = {},
  enabled = true,
}) {
  const [options, setOptions]       = useState([]);
  const [isLoading, setIsLoading]   = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentTerm, setCurrentTerm] = useState('');
  const [hasMore, setHasMore]       = useState(true);

  // Serialise extraParams so useEffect dependency comparison works
  const extraKey = JSON.stringify(extraParams);

  const fetchPage = useCallback(async (page, search, replace = false) => {
    if (!enabled) return;
    setIsLoading(true);
    const data = await CommonService.getEntities(app, entity, status, search, page, extraParams);
    const items = data?.items ?? [];
    const count = data?.count ?? 0;
    const newOptions = items.map((item) => ({
      value: item.id,
      label: item.name,
      raw:   item,
    }));
    setHasMore(page * pageSize < count);
    if (replace || search !== '') {
      setOptions(newOptions);
    } else {
      // Append, preserving any already-selected options not in the new page
      setOptions((prev) => {
        const incomingIds = new Set(newOptions.map((o) => o.value));
        const kept = prev.filter((o) => !incomingIds.has(o.value));
        return [...kept, ...newOptions];
      });
    }
    setIsLoading(false);
  }, [app, entity, status, extraKey, enabled]); // eslint-disable-line react-hooks/exhaustive-deps

  // Initial load / reload when extraParams or enabled changes
  useEffect(() => {
    if (!enabled) {
      setOptions([]);
      setCurrentPage(1);
      setCurrentTerm('');
      setHasMore(true);
      return;
    }
    setCurrentPage(1);
    setCurrentTerm('');
    fetchPage(1, '', true);
  }, [enabled, extraKey]); // eslint-disable-line react-hooks/exhaustive-deps

  // Debounced search handler
  const debounce = (fn, delay) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  };

  const handleInputChange = useMemo(() => debounce((term) => {
    setCurrentPage(1);
    setCurrentTerm(term);
    fetchPage(1, term, true);
  }, 350), [fetchPage]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleMenuScrollToBottom = useCallback(() => {
    if (isLoading || !hasMore) return;
    const nextPage = currentPage + 1;
    setCurrentPage(nextPage);
    fetchPage(nextPage, currentTerm, false);
  }, [isLoading, hasMore, currentPage, currentTerm, fetchPage]);

  const reset = useCallback(() => {
    setOptions([]);
    setCurrentPage(1);
    setCurrentTerm('');
    setHasMore(true);
  }, []);

  return {
    options,
    isLoading,
    onInputChange:        handleInputChange,
    onMenuScrollToBottom: handleMenuScrollToBottom,
    reset,
  };
}
