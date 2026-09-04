import { useMemo, useState } from 'react';
import { useFormContext } from 'react-hook-form';
import Button from 'react-bootstrap/Button';
import Spinner from 'react-bootstrap/Spinner';
import { IoCloudDownloadOutline as SourceIcon } from 'react-icons/io5';
import {
  appLookup, sandboxLookup, QUOTA_EXHAUSTED, RATE_LIMITED, REFUSED,
} from '../services/lookup.service';

/**
 * "Fill this form from an external source."
 *
 * SCOPE_external_data_sources.md@d2de531 §4. The user types, presses the
 * source's button, picks a result — **and the form fills**. Nothing is written:
 * the record is created by the ordinary submit below, with its required-field
 * check, its role gate, its computed fields, its geo and numeric normalisation
 * and its row-visibility rule all intact.
 *
 * Mounted through the `formLookups` registry slot, so `common/` never imports
 * this module and an application that declares no source renders exactly
 * today's plain form (§10 item 1).
 *
 * The three failures are rendered honestly (§8.4). A source that could not be
 * reached **keeps what the user typed** and badges the button; a refusal says it
 * is the key; an exhausted quota says so in those words. What is never done is
 * showing an empty result list for any of them — an empty list that actually
 * means *you have run out* is the `route-not-found`-vs-`engine-unavailable`
 * mistake in a new module.
 *
 * The payload is **data** (D10): every value is rendered as text into a form
 * input. Nothing here sets innerHTML, and nothing here reaches a prompt.
 */
const LookupControl = ({ sources = [], sandboxToken = '', entityName = '',
                         viewAs = null, viewAsId = '1',
                         transport: injected, t = (k) => k, disabled = false }) => {
  const { setValue, getValues } = useFormContext();
  // The control picks its own transport, so the HOST imports nothing from this
  // module — not even a service. `common/` and the sandbox form reach all of
  // this through the registry contribution and nothing else (§10 item 1).
  // `transport` stays injectable for tests.
  // The claimed preview role travels with the request (D5: the gate is the
  // entity's own WRITE role). It arrives as a prop rather than being read from
  // the sandbox service, because `datasource` never imports `generator` — the
  // same reason this control is reached through a registry slot at all.
  const transport = useMemo(
    () => injected || (sandboxToken
      ? sandboxLookup(sandboxToken, entityName, viewAs, viewAsId)
      : appLookup(entityName)),
    [injected, sandboxToken, entityName, viewAs, viewAsId],
  );
  const [openSource, setOpenSource] = useState(null);
  const [query, setQuery]           = useState('');
  const [busy, setBusy]             = useState(false);
  const [candidates, setCandidates] = useState(null);
  const [failure, setFailure]       = useState(null);

  if (!sources.length) return null;

  const open = (source) => {
    setOpenSource(source);
    setCandidates(null);
    setFailure(null);
    // Seed the box with whatever the user has already typed in the field most
    // likely to be the title — the search they were about to type by hand.
    const values = getValues() || {};
    const seed = source.fields.map((f) => values[f]).find((v) => typeof v === 'string' && v.trim());
    setQuery(seed || '');
  };

  const search = async () => {
    if (!query.trim()) return;
    setBusy(true);
    setFailure(null);
    const outcome = await transport.search(openSource.id, query.trim());
    setBusy(false);
    if (!outcome.ok) { setFailure(outcome); setCandidates(null); return; }
    setCandidates(outcome.candidates);
  };

  const fill = async (candidate) => {
    let values = candidate.values;
    if (openSource.two_step && candidate.id) {
      // The pick fires the second request (§4.2) — two requests, one user
      // action. A failure here leaves the form untouched rather than filling it
      // with the search result's thinner values, which would look like success.
      setBusy(true);
      const outcome = await transport.detail(openSource.id, candidate.id);
      setBusy(false);
      if (!outcome.ok) { setFailure(outcome); return; }
      values = outcome.values;
    }
    Object.entries(values || {}).forEach(([field, value]) => {
      // `shouldDirty`/`shouldValidate` so the form behaves as if the user typed
      // it — which they may now edit freely, because a suggestion is a
      // suggestion.
      setValue(field, value, { shouldDirty: true, shouldValidate: true });
    });
    setOpenSource(null);
    setCandidates(null);
  };

  const failureText = (outcome) => {
    if (!outcome) return '';
    if (outcome.key === REFUSED) {
      return outcome.sourceStatus
        ? `${t(REFUSED)} (${outcome.sourceStatus})`
        : t(REFUSED);
    }
    if (outcome.key === QUOTA_EXHAUSTED) return t(QUOTA_EXHAUSTED);
    if (outcome.key === RATE_LIMITED) return t('datasource-rate-limited');
    return t(outcome.key);
  };

  return (
    <div className="migratis-field datasource-lookup" data-testid="lookup-control">
      <div className="d-flex flex-wrap gap-2">
        {sources.map((source) => (
          <Button key={source.id} type="button" size="sm" variant="outline-secondary"
                  disabled={disabled}
                  onClick={() => (openSource?.id === source.id ? setOpenSource(null) : open(source))}>
            <SourceIcon /> {source.label}
          </Button>
        ))}
      </div>

      {openSource && (
        <div className="mt-2" data-testid="lookup-panel">
          <div className="d-flex gap-2">
            <input className="form-control" value={query} autoFocus
                   aria-label={openSource.label}
                   placeholder={t('datasource-search-placeholder')}
                   onChange={(e) => setQuery(e.target.value)}
                   onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); search(); } }} />
            <Button type="button" onClick={search} disabled={busy || !query.trim()}>
              {busy ? <Spinner size="sm" animation="border" /> : t('datasource-search')}
            </Button>
          </div>

          {failure && (
            /* The edit is kept — the box still holds what was typed. */
            <div className="text-danger small mt-2" data-testid="lookup-failure">
              {failureText(failure)}
            </div>
          )}

          {candidates && candidates.length === 0 && !failure && (
            /* A real answer, and told apart from every failure above. */
            <div className="text-muted small mt-2" data-testid="lookup-empty">
              {t('datasource-no-candidates')}
            </div>
          )}

          {candidates && candidates.length > 0 && (
            <ul className="list-group mt-2" data-testid="lookup-candidates">
              {candidates.map((candidate, index) => (
                <li key={candidate.id || index}
                    className="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                  <span>{candidate.label}</span>
                  <Button type="button" size="sm" disabled={busy}
                          onClick={() => fill(candidate)}>
                    {t('datasource-use-this')}
                  </Button>
                </li>
              ))}
            </ul>
          )}
          <div className="form-text text-muted mt-1">{t('datasource-fills-help')}</div>
        </div>
      )}
    </div>
  );
};

export default LookupControl;
