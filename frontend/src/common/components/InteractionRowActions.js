import Button from 'react-bootstrap/Button';
import { getVisibleInteractions } from './interactionVisibility';

// Per-record cluster of workflow-step buttons, reused by every display mode
// (table, cards, list, kanban, masonry, gallery, calendar, grid). The shape
// of the click payload — `__source_id`, an optional `link_via` prefill, and
// `__step_id` — is the contract `Sandbox.handleInteraction` expects, so the
// same handler routes form/direct_create/pick_assign across all modes.
//
// Returns null (no DOM at all) when:
//   - the entity has no interactions[]
//   - the caller did not pass an onInteraction handler
//   - getVisibleInteractions filters everything out for this record/viewer
//     (precondition not met, prereq incomplete, actor_role mismatch, etc.)
//
// Callers can override visual presentation via `className`, `buttonVariant`,
// `buttonSize` to fit the host display's density (e.g. calendar chips need
// tighter sizing than card grids).
export const InteractionRowActions = ({
  interactions,
  recordData,
  recordId,
  parentRecordData,
  viewAs,
  getRoleRank,
  onInteraction,
  className = 'd-flex flex-wrap gap-1',
  buttonVariant = 'outline-primary',
  buttonSize = 'sm',
}) => {
  if (!Array.isArray(interactions) || interactions.length === 0) return null;
  if (!onInteraction) return null;

  const visible = getVisibleInteractions(
    interactions, recordData, parentRecordData, viewAs, getRoleRank,
  );
  if (visible.length === 0) return null;

  return (
    <div className={className}>
      {visible.map((it, i) => {
        const isPickAssign = it.mode === 'pick_assign';
        const prefill = {
          ...(it.default_prefill || {}),
          __source_id: recordId,
          ...(!isPickAssign && it.link_via ? { [it.link_via]: recordId } : {}),
          ...(it.step_id ? { __step_id: it.step_id } : {}),
        };
        return (
          <Button
            key={i}
            size={buttonSize}
            variant={buttonVariant}
            onClick={(e) => {
              // Some display modes have outer click handlers (kanban cards
              // call onEdit on click, calendar chips call onEdit, grid
              // cells call onEdit) — stop propagation so clicking a workflow
              // button never also opens the edit modal underneath.
              e.stopPropagation();
              onInteraction(it.target, prefill, it.mode || 'form');
            }}
            title={it.description || it.trigger_label || it.trigger || `${it.action} ${it.target}`}
          >
            {it.trigger_label || it.trigger || `${it.action} → ${it.target}`}
          </Button>
        );
      })}
    </div>
  );
};

export default InteractionRowActions;
