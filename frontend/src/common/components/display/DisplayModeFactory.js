import TableDisplay from './TableDisplay';
import CardsDisplay from './CardsDisplay';
import MasonryDisplay from './MasonryDisplay';
import KanbanDisplay from './KanbanDisplay';
import ListDisplay from './ListDisplay';
import GalleryDisplay from './GalleryDisplay';
import CalendarDisplay from './CalendarDisplay';
import GridDisplay from './GridDisplay';
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
};

export const getDisplayMode = (mode) => {
  return DISPLAY_MODE_MAP[mode] || TableDisplay;
};

const DynamicDisplay = ({ displayMode, entityConfig, sandboxConfig, ...props }) => {
  if (displayMode === 'custom_display') {
    const fallbackMode = entityConfig?.display_mode_options?.custom_display?.fallback_display_mode || 'table';
    const FallbackDisplay = getDisplayMode(fallbackMode);
    return (
      <CustomDisplay
        entityConfig={entityConfig}
        sandboxConfig={sandboxConfig}
        FallbackDisplay={FallbackDisplay}
        {...props}
      />
    );
  }
  const DisplayComponent = getDisplayMode(displayMode);
  return <DisplayComponent entityConfig={entityConfig} sandboxConfig={sandboxConfig} {...props} />;
};

export default DynamicDisplay;
