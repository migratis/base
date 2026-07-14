import TableDisplay from './TableDisplay';
import CardsDisplay from './CardsDisplay';
import MasonryDisplay from './MasonryDisplay';
import KanbanDisplay from './KanbanDisplay';
import ListDisplay from './ListDisplay';
import GalleryDisplay from './GalleryDisplay';
import CalendarDisplay from './CalendarDisplay';
import GridDisplay from './GridDisplay';
import HubDetailDisplay from './HubDetailDisplay';
import CustomDisplay from './CustomDisplay';

export const DISPLAY_MODE_MAP = {
  table: TableDisplay,
  cards: CardsDisplay,
  masonry: MasonryDisplay,
  kanban: KanbanDisplay,
  list: ListDisplay,
  gallery: GalleryDisplay,
  calendar: CalendarDisplay,
  grid: GridDisplay,
  hub_detail: HubDetailDisplay,
};

export const getDisplayMode = (mode) => {
  return DISPLAY_MODE_MAP[mode] || TableDisplay;
};

/**
 * A hub entity (some other entity embeds into it) whose custom_display fails
 * degrades to the deterministic `hub_detail` composite rather than the plain
 * table/cards floor (GAP_ANALYSIS_agent_lane_poc15.md §1): the whole point of
 * the composite-display rail is that a hub is never shown as a bare grid, so
 * neither is its fallback. An explicit `fallback_display_mode` still wins.
 */
export const isHubEntity = (entity, sandboxConfig) => {
  if (!entity) return false;
  const entities = sandboxConfig?.entities || {};
  return Object.values(entities).some(
    (ec) => ec && typeof ec === 'object' && ec.embed_in_parent === entity.name,
  );
};

const DynamicDisplay = ({ displayMode, entity, entityConfig, sandboxConfig, ...props }) => {
  if (displayMode === 'custom_display') {
    const fallbackMode = entityConfig?.display_mode_options?.custom_display?.fallback_display_mode
      || (isHubEntity(entity, sandboxConfig) ? 'hub_detail' : 'table');
    const FallbackDisplay = getDisplayMode(fallbackMode);
    return (
      <CustomDisplay
        entity={entity}
        entityConfig={entityConfig}
        sandboxConfig={sandboxConfig}
        FallbackDisplay={FallbackDisplay}
        {...props}
      />
    );
  }
  const DisplayComponent = getDisplayMode(displayMode);
  return <DisplayComponent entity={entity} entityConfig={entityConfig} sandboxConfig={sandboxConfig} {...props} />;
};

export default DynamicDisplay;
