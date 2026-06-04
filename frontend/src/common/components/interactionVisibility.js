// Helpers that decide, for a given record, which workflow interactions on its
// entity should still be shown. Two reasons to drop a button:
//
//   1. The step has already been done for THIS record (its `completion`
//      predicate matches `record.data`). Example: pick_assign on Order with
//      `link_via: shipping_method` — once shipping_method is set, hide the
//      "Choose shipping method" button.
//
//   2. An earlier step in the same source-chain is not yet done (one of the
//      `prereq_step_ids` is still incomplete on this record). Example: the
//      "Proceed to payment" button is hidden until "Choose shipping method"
//      is complete.
//
// Both completion and prereq_step_ids are populated server-side in
// `enrich_workflow_interactions`. When they are absent (older configs, or
// steps with no deterministic completion signal) the helpers degrade to
// showing the button — never hide on a guess.
//
// `from_parent` items belong to the parent's chain. The caller should pass
// the PARENT record's data for those; for everything else, pass the row's
// own record. `getVisibleInteractions` handles the split when both records
// are provided.

// SandboxForm's SelectField stores enum / choice values as
// `{label, value}` dicts; FK fields can store the same shape. Unwrap the
// `.value` so predicate comparisons see the semantic value, not the option
// object. Bare scalars pass through unchanged.
const _unwrapSelectValue = (v) => {
  if (v && typeof v === 'object' && !Array.isArray(v) && 'value' in v) {
    return v.value;
  }
  return v;
};

const _matchPredicate = (predicate, data) => {
  if (!predicate || typeof predicate !== 'object') return false;
  if (!data || typeof data !== 'object') return false;
  const value = _unwrapSelectValue(data[predicate.field]);
  if (predicate.op === 'truthy') {
    return value !== undefined && value !== null && value !== '' && value !== false;
  }
  if (predicate.op === 'equals') {
    if (value === undefined || value === null) return false;
    // String-compare so '1' === 1 lines up with the backend storage layer
    // (it writes string outcomes like "paid" but record.data may store
    // numeric statuses as integers).
    return String(value) === String(predicate.value);
  }
  return false;
};

const _isComplete = (interaction, data) => {
  if (!interaction || typeof interaction !== 'object') return false;
  if (!interaction.completion) return false;
  return _matchPredicate(interaction.completion, data);
};

// A branched step carries a `precondition` predicate set by enrich_interactions
// from WorkflowStep.precondition_field / .precondition_value. The button only
// surfaces when the source record matches — that is what makes alternative
// branches actually selective at runtime.
const _preconditionSatisfied = (interaction, data) => {
  if (!interaction || typeof interaction !== 'object') return true;
  if (!interaction.precondition) return true;
  return _matchPredicate(interaction.precondition, data);
};

// `actor_role` on a workflow interaction is a STRICT allow-list, not a ladder.
// Empty / missing → no per-step gate (entity-level write role still applies
// on the API side). Any non-empty value — INCLUDING the application's
// anonymous role — requires exact equality with the viewer's role. There is
// no catch-all for the anonymous tier; if a step is "open to everyone",
// leave actor_role empty and let the entity-level min_write_role govern.
const _roleAllowed = (interaction, viewerRole) => {
  if (!interaction || typeof interaction !== 'object') return true;
  const gate = (interaction.actor_role || '').trim();
  if (!gate) return true;
  const viewer = (viewerRole || '').trim();
  return viewer === gate;
};

// Stage A — ladder check against the SOURCE entity's `min_write_role`.
// Each enriched interaction carries `entity_min_write_role`, the name of the
// role required to act on the source entity (the row whose card hosts the
// button). The viewer's rank must be >= that floor before we even consider
// the strict per-step gate (Stage B). When the caller has no `getRoleRank`
// function (legacy sandbox configs without ApplicationRole) we degrade to
// "show" — Stage A is best-effort, Stage B is still enforced.
const _stageAAllowed = (interaction, viewerRole, getRoleRank) => {
  if (!interaction || typeof interaction !== 'object') return true;
  const floor = interaction.entity_min_write_role;
  if (!floor) return true;
  if (typeof getRoleRank !== 'function') return true;
  const viewerRank = getRoleRank((viewerRole || '').trim());
  const floorRank = getRoleRank(floor);
  if (viewerRank == null || floorRank == null) return true;
  return viewerRank >= floorRank;
};

/**
 * Filter an interactions array per-record.
 *
 * @param {Array}    interactions      The entityConfig.interactions array.
 * @param {Object}   recordData        record.data for own-chain items.
 * @param {Object}   parentRecordData  record.data of the parent (for
 *                                     from_parent items). Optional;
 *                                     defaults to recordData.
 * @param {string}   viewerRole        The role the viewer claims (from the
 *                                     sandbox view_as selector).
 * @param {Function} getRoleRank       Optional name→rank lookup injected
 *                                     from the sandbox config. Required for
 *                                     Stage A narrowing; absent → Stage A
 *                                     is skipped.
 * @returns {Array} the subset to render.
 */
export function getVisibleInteractions(interactions, recordData, parentRecordData, viewerRole, getRoleRank) {
  if (!Array.isArray(interactions) || interactions.length === 0) return [];
  const ownData    = recordData       || {};
  const parentData = parentRecordData || ownData;

  // Build a step_id → {interaction, data} map so prereq lookups consult the
  // same record context that gates the prereq itself.
  const byStepId = new Map();
  for (const it of interactions) {
    if (!it || typeof it !== 'object' || it.step_id == null) continue;
    const data = it.from_parent ? parentData : ownData;
    byStepId.set(it.step_id, { interaction: it, data });
  }

  return interactions.filter((it) => {
    if (!it || typeof it !== 'object') return true;
    const data = it.from_parent ? parentData : ownData;
    if (_isComplete(it, data)) return false;
    if (!_preconditionSatisfied(it, data)) return false;
    if (!_stageAAllowed(it, viewerRole, getRoleRank)) return false;
    if (!_roleAllowed(it, viewerRole)) return false;
    const prereqs = Array.isArray(it.prereq_step_ids) ? it.prereq_step_ids : [];
    for (const prereqId of prereqs) {
      const prereq = byStepId.get(prereqId);
      if (!prereq) continue;
      // Prereqs with no deterministic completion signal (e.g. form-mode
      // creates whose downstream status flip happens in a chained child)
      // can't be evaluated. Per this file's docstring we degrade to showing
      // the button rather than hiding on a guess.
      if (!prereq.interaction?.completion) continue;
      if (!_isComplete(prereq.interaction, prereq.data)) return false;
    }
    return true;
  });
}

/**
 * True when ANY interaction would survive the per-record filter — useful for
 * deciding whether to render the container element (border-top, gap, etc.).
 */
export function hasVisibleInteractions(interactions, recordData, parentRecordData) {
  return getVisibleInteractions(interactions, recordData, parentRecordData).length > 0;
}
