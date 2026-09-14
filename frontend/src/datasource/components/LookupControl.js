import { Fragment, useMemo, useState } from 'react';
import { useFormContext } from 'react-hook-form';
import Button from 'react-bootstrap/Button';
import Spinner from 'react-bootstrap/Spinner';
import { IoCloudDownloadOutline as SourceIcon,
         IoImageOutline as NoImageIcon } from 'react-icons/io5';
import {
  appLookup, sandboxLookup,
  UNAVAILABLE, QUOTA_EXHAUSTED, RATE_LIMITED, REFUSED,
} from '../services/lookup.service';
import { describeCandidate } from '../candidatePreview';

/**
 * What each failure says when the host translates none of it.
 *
 * Every `t()` in this file carries a fallback, and these are the ones a key
 * alone cannot supply. `LookupControl` is mounted with the CALLER's translator
 * (`formLookups`), and it has three hosts with three vocabularies: the
 * designer's pages (the `generator` namespace), a generated application (its
 * own, seeded by codegen's `_SHARED_COMPONENT_TRANSLATIONS`) — and the sandbox
 * preview, which speaks the APPLICATION's vocabulary and has never carried a
 * word about data sources, so every key rendered itself. `ExportButton`, the
 * other framework component the sandbox mounts this way, has always passed a
 * fallback on every call; this is that rule, kept by a test rather than by
 * memory.
 */
const FALLBACKS = {
  [UNAVAILABLE]:     'The source could not be reached. What you typed has been kept.',
  [REFUSED]:         'The source refused the request — its key may be missing or no longer valid.',
  [QUOTA_EXHAUSTED]: 'This application has used all its lookups for today.',
  [RATE_LIMITED]:    'Too many searches just now — try again in a moment.',
};

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
 * input. Nothing here sets innerHTML, and nothing here reaches a prompt. The
 * single exception is the candidate poster, which is an `<img src>` and
 * therefore fetches — so it is taken only from a field the design declares
 * `image`, only when the value is https or an inline image, and always with
 * `referrerPolicy="no-referrer"`. See `../candidatePreview.js`, which decides
 * what a row says; this file decides how it looks.
 */
/**
 * One candidate, as something a person can choose between.
 *
 * The whole row is the control — a poster, a label and four facts are one
 * target, not a caption beside a button — so it is a `<button>` and the "use
 * this" wording is the affordance inside it rather than a second, nested one.
 * The accessible name is therefore the row's own text, which is exactly what a
 * screen reader needs read out to make the same choice.
 *
 * `referrerPolicy="no-referrer"` on the poster: this is the one element here
 * that fetches, and the source's CDN has no business learning which deployment
 * — or which sandbox token — a designer is looking at. `alt=""` because the
 * label right beside it is the picture's text; announcing a filename twice
 * helps nobody.
 */
const CandidateRow = ({ candidate, preview, reserveThumb, twoStep, busy, onPick, t }) => {
  const { thumbnail, facts, fillCount } = preview;
  return (
    <button type="button" disabled={busy} onClick={onPick}
            data-testid="lookup-candidate"
            className="list-group-item list-group-item-action lookup-candidate">
      {thumbnail ? (
        <img className="lookup-candidate-thumb" src={thumbnail.src} alt=""
             loading="lazy" referrerPolicy="no-referrer" />
      ) : reserveThumb ? (
        /* A source that published a poster for one result and not the next
           would otherwise hand back a ragged list; the slot stays. */
        <span className="lookup-candidate-thumb lookup-candidate-thumb--empty"
              aria-hidden="true"><NoImageIcon /></span>
      ) : null}

      <span className="lookup-candidate-body">
        <span className="lookup-candidate-title">{candidate.label}</span>
        {facts.length > 0 && (
          <span className="lookup-candidate-facts">
            {facts.map((fact) => (
              <Fragment key={fact.field}>
                <span className="lookup-candidate-fact-label">{fact.label}</span>
                <span className="lookup-candidate-fact-value">{fact.text}</span>
              </Fragment>
            ))}
          </span>
        )}
      </span>

      <span className="lookup-candidate-action">
        {/* What the pick will do, said before it is made. A two-step source
            answers its search with a thinner row than the pick will fetch
            (§4.2), so counting what is on screen would understate it — and a
            row that promises three fields and fills eleven is the kind of
            small lie that makes the honest numbers unbelievable too. */}
        <span className="lookup-candidate-fills">
          {twoStep ? t('datasource-fills-on-pick',
                       'Full details are fetched when you choose this')
                   : t('datasource-fills-count',
                       { count: fillCount, defaultValue: 'Fills {{count}} fields' })}
        </span>
        <span className="btn btn-sm btn-primary lookup-candidate-cta">
          {t('datasource-use-this', 'Use this')}
        </span>
      </span>
    </button>
  );
};

/** The control itself: the source buttons, the search box, and the list of
 *  candidates `CandidateRow` above renders one of. */
const LookupControl = ({ sources = [], sandboxToken = '', entityName = '',
                         viewAs = null, viewAsId = '1', fillable = null,
                         fieldMeta = null,
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

  // What each row says, decided once per answer rather than per render — and
  // before the early return below, so the hook order never depends on whether
  // this entity declares a source.
  const described = useMemo(
    () => (candidates || []).map((candidate) => ({
      candidate,
      preview: describeCandidate(candidate, { fieldMeta, fillable }),
    })),
    [candidates, fieldMeta, fillable],
  );
  const anyThumbnail = described.some(({ preview }) => preview.thumbnail);

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
    // On an existing record the form has fields the user may not touch —
    // `read_only_after_create`, and anything the config marks uneditable. The
    // control renders above them and must not write past a rule the form is
    // stating on screen, so the host names what it is letting the user edit.
    // `null` is "no restriction", which is the create form and every earlier
    // caller.
    const allowed = Array.isArray(fillable) ? new Set(fillable) : null;
    Object.entries(values || {}).forEach(([field, value]) => {
      if (allowed && !allowed.has(field)) return;
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
        ? `${t(REFUSED, FALLBACKS[REFUSED])} (${outcome.sourceStatus})`
        : t(REFUSED, FALLBACKS[REFUSED]);
    }
    if (outcome.key === QUOTA_EXHAUSTED) return t(QUOTA_EXHAUSTED, FALLBACKS[QUOTA_EXHAUSTED]);
    if (outcome.key === RATE_LIMITED) return t(RATE_LIMITED, FALLBACKS[RATE_LIMITED]);
    return t(outcome.key, FALLBACKS[outcome.key] || FALLBACKS[UNAVAILABLE]);
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
                   placeholder={t('datasource-search-placeholder',
                                  'What are you looking for?')}
                   onChange={(e) => setQuery(e.target.value)}
                   onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); search(); } }} />
            <Button type="button" onClick={search} disabled={busy || !query.trim()}>
              {busy ? <Spinner size="sm" animation="border" /> : t('datasource-search', 'Search')}
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
              {t('datasource-no-candidates', 'Nothing found')}
            </div>
          )}

          {candidates && candidates.length > 0 && (
            <div className="list-group mt-2" data-testid="lookup-candidates">
              {described.map(({ candidate, preview }, index) => (
                <CandidateRow key={candidate.id || index}
                              candidate={candidate} preview={preview}
                              reserveThumb={anyThumbnail} twoStep={!!openSource.two_step}
                              busy={busy} t={t} onPick={() => fill(candidate)} />
              ))}
            </div>
          )}
          <div className="form-text text-muted mt-1">{t('datasource-fills-help',
                  'Choosing a result fills the form. You can change anything before saving.')}</div>
        </div>
      )}
    </div>
  );
};

export default LookupControl;
