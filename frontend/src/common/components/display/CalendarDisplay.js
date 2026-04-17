import { useState, useMemo } from 'react';
import Button from 'react-bootstrap/Button';
import Badge from 'react-bootstrap/Badge';
import {
  startOfMonth, endOfMonth,
  startOfWeek, endOfWeek,
  eachDayOfInterval,
  isSameMonth, isSameDay,
  format, addMonths, subMonths,
  addWeeks, subWeeks,
  parseISO, isValid,
} from 'date-fns';
import {
  IoChevronBackOutline as PrevIcon,
  IoChevronForwardOutline as NextIcon,
  IoTrashOutline as TrashIcon,
} from 'react-icons/io5';

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------

/** Parse any date string / ISO string / Date into a JS Date (or null). */
const parseDate = (value) => {
  if (!value) return null;
  if (value instanceof Date) return isValid(value) ? value : null;
  try {
    const d = parseISO(String(value));
    return isValid(d) ? d : null;
  } catch {
    return null;
  }
};

/** Auto-detect the start date field name from entity field definitions. */
const detectStartField = (fields) => {
  const candidates = [
    'start_date', 'start_at', 'starts_at', 'date', 'scheduled_at',
    'planned_date', 'intervention_date', 'appointment_date',
    'event_date', 'begins_at', 'planned_at', 'created_at',
  ];
  for (const c of candidates) {
    if (fields.find((f) => f.name === c)) return c;
  }
  // Fall back to the first date/datetime field found
  return fields.find((f) => ['date', 'datetime'].includes(f.field_type))?.name || null;
};

/**
 * Scan actual record data keys to find the first one that contains valid date values.
 * Used as a last-resort fallback when field config/auto-detection fails.
 */
const detectStartFieldFromRecords = (records) => {
  if (!records.length) return null;
  const sample = records.slice(0, 5);
  const keys = Object.keys(sample[0]?.data || {});
  for (const key of keys) {
    const hasValidDate = sample.some((r) => parseDate(r.data[key]) !== null);
    if (hasValidDate) return key;
  }
  return null;
};

/** Auto-detect a title field from entity fields. */
const detectTitleField = (fields) => {
  const candidates = ['title', 'name', 'label', 'subject', 'description'];
  for (const c of candidates) {
    if (fields.find((f) => f.name === c)) return c;
  }
  return fields.find((f) => f.field_type === 'string')?.name || null;
};

/** Map a category/status value to a Bootstrap color variant. */
const VALUE_COLORS = [
  'primary', 'success', 'danger', 'warning', 'info', 'secondary',
  'dark',
];
const colorFor = (() => {
  const cache = {};
  let idx = 0;
  return (value) => {
    if (!value) return 'primary';
    const key = String(value);
    if (!(key in cache)) {
      cache[key] = VALUE_COLORS[idx % VALUE_COLORS.length];
      idx++;
    }
    return cache[key];
  };
})();

// -------------------------------------------------------------------
// Sub-components
// -------------------------------------------------------------------

const EventChip = ({ record, titleField, colorVariant, onEdit, onDelete }) => {
  const title = titleField ? record.data[titleField] : null;
  const label = title ? String(title) : '—';

  return (
    <div
      className={`d-flex align-items-center gap-1 rounded px-1 mb-1`}
      style={{
        background: `var(--bs-${colorVariant}-bg, #e7f0ff)`,
        border: `1px solid var(--bs-${colorVariant}, #0d6efd)`,
        fontSize: '0.72rem',
        cursor: onEdit ? 'pointer' : 'default',
        overflow: 'hidden',
      }}
      onClick={(e) => { e.stopPropagation(); if (onEdit) onEdit(record); }}
    >
      <span
        style={{
          flex: 1,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: `var(--bs-${colorVariant}-text, #0a58ca)`,
          fontWeight: 500,
        }}
        title={label}
      >
        {label}
      </span>
      {onDelete && (
        <span
          className="link action"
          style={{ flexShrink: 0, fontSize: '0.8rem' }}
          onClick={(e) => { e.stopPropagation(); onDelete(record.id); }}
        >
          <TrashIcon />
        </span>
      )}
    </div>
  );
};

// -------------------------------------------------------------------
// Main component
// -------------------------------------------------------------------


const CalendarDisplay = ({
  entity,
  records,
  config = {},
  onEdit,
  onDelete,
  onAdd,
  t,
}) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback || key);

  const opts = config?.display_mode_options || {};
  const fields = entity?.fields || [];

  // Resolve field names — prefer explicit config, then auto-detection from schema,
  // then last-resort scan of actual record data keys.
  const startField = opts.calendar_start_field
    || detectStartField(fields)
    || detectStartFieldFromRecords(records);
  const endField   = opts.calendar_end_field   || null;
  const titleField = opts.calendar_title_field || detectTitleField(fields);
  const colorField = opts.calendar_color_field || null;

  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState('month'); // 'month' | 'week'

  // Build event map: day key → [records]
  const eventsByDay = useMemo(() => {
    const map = {};
    if (!startField) return map;

    records.forEach((record) => {
      const startDate = parseDate(record.data[startField]);
      if (!startDate) return;

      const endDate = endField ? parseDate(record.data[endField]) : null;

      // Span all days from start to end (inclusive), capped to avoid huge ranges.
      const rangeEnd = endDate && endDate > startDate ? endDate : startDate;
      const days = eachDayOfInterval({ start: startDate, end: rangeEnd });
      const capped = days.slice(0, 30); // safety cap

      capped.forEach((day) => {
        const key = format(day, 'yyyy-MM-dd');
        if (!map[key]) map[key] = [];
        map[key].push(record);
      });
    });

    return map;
  }, [records, startField, endField]);

  // Compute the grid days
  const days = useMemo(() => {
    if (view === 'month') {
      const monthStart = startOfMonth(currentDate);
      const monthEnd   = endOfMonth(currentDate);
      const gridStart  = startOfWeek(monthStart, { weekStartsOn: 1 });
      const gridEnd    = endOfWeek(monthEnd, { weekStartsOn: 1 });
      return eachDayOfInterval({ start: gridStart, end: gridEnd });
    }
    // week view
    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
    const weekEnd   = endOfWeek(currentDate, { weekStartsOn: 1 });
    return eachDayOfInterval({ start: weekStart, end: weekEnd });
  }, [currentDate, view]);

  const goBack = () => {
    setCurrentDate(view === 'month' ? subMonths(currentDate, 1) : subWeeks(currentDate, 1));
  };
  const goForward = () => {
    setCurrentDate(view === 'month' ? addMonths(currentDate, 1) : addWeeks(currentDate, 1));
  };
  const goToday = () => setCurrentDate(new Date());

  const headerLabel = view === 'month'
    ? format(currentDate, 'MMMM yyyy')
    : `${format(days[0], 'dd MMM')} – ${format(days[6], 'dd MMM yyyy')}`;

  const today = new Date();

  const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div>
      {/* Toolbar */}
      <div className="d-flex align-items-center justify-content-between mb-2 flex-wrap gap-2">
        <div className="d-flex align-items-center gap-2">
          <Button variant="outline-secondary" size="sm" onClick={goBack}>
            <PrevIcon />
          </Button>
          <Button variant="outline-secondary" size="sm" onClick={goToday}>
            {tval('calendar-today', 'Today')}
          </Button>
          <Button variant="outline-secondary" size="sm" onClick={goForward}>
            <NextIcon />
          </Button>
          <span style={{ fontWeight: 600, minWidth: '160px' }}>{headerLabel}</span>
        </div>
        <div className="d-flex gap-1">
          <Button
            size="sm"
            variant={view === 'month' ? 'primary' : 'outline-secondary'}
            onClick={() => setView('month')}
          >
            {tval('calendar-month', 'Month')}
          </Button>
          <Button
            size="sm"
            variant={view === 'week' ? 'primary' : 'outline-secondary'}
            onClick={() => setView('week')}
          >
            {tval('calendar-week', 'Week')}
          </Button>
        </div>
      </div>

      {/* Calendar grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, 1fr)',
          border: '1px solid #dee2e6',
          borderRadius: '0.375rem',
          overflow: 'hidden',
        }}
      >
        {/* Day name headers */}
        {DAY_NAMES.map((d) => (
          <div
            key={d}
            style={{
              padding: '6px 4px',
              textAlign: 'center',
              fontWeight: 600,
              fontSize: '0.78rem',
              background: '#f8f9fa',
              borderBottom: '1px solid #dee2e6',
              color: '#495057',
            }}
          >
            {d}
          </div>
        ))}

        {/* Day cells */}
        {days.map((day) => {
          const key = format(day, 'yyyy-MM-dd');
          const dayEvents = eventsByDay[key] || [];
          const isToday = isSameDay(day, today);
          const isCurrentMonth = view === 'week' ? true : isSameMonth(day, currentDate);
          const MAX_VISIBLE = 3;
          const overflow = dayEvents.length - MAX_VISIBLE;

          return (
            <div
              key={key}
              onClick={onAdd ? () => onAdd(key) : undefined}
              style={{
                minHeight: view === 'month' ? '90px' : '140px',
                padding: '4px',
                borderRight: '1px solid #dee2e6',
                borderBottom: '1px solid #dee2e6',
                background: isToday ? '#fff8e1' : 'white',
                opacity: isCurrentMonth ? 1 : 0.45,
                verticalAlign: 'top',
                overflow: 'hidden',
                cursor: onAdd ? 'pointer' : 'default',
              }}
            >
              {/* Day number */}
              <div
                style={{
                  fontWeight: isToday ? 700 : 400,
                  fontSize: '0.8rem',
                  marginBottom: '3px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                {isToday ? (
                  <Badge bg="primary" style={{ borderRadius: '50%', width: '22px', height: '22px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>
                    {format(day, 'd')}
                  </Badge>
                ) : (
                  <span style={{ color: '#495057' }}>{format(day, 'd')}</span>
                )}
              </div>

              {/* Events */}
              {dayEvents.slice(0, MAX_VISIBLE).map((record) => {
                const colorValue = colorField ? record.data[colorField] : null;
                const variant = colorFor(colorValue);
                return (
                  <EventChip
                    key={record.id}
                    record={record}
                    titleField={titleField}
                    colorVariant={variant}
                    onEdit={onEdit}
                    onDelete={onDelete}
                  />
                );
              })}

              {overflow > 0 && (
                <div
                  style={{ fontSize: '0.7rem', color: '#6c757d', cursor: onEdit ? 'pointer' : 'default' }}
                  onClick={onEdit ? (e) => { e.stopPropagation(); onEdit(dayEvents[MAX_VISIBLE]); } : undefined}
                >
                  +{overflow} {tval('calendar-more', 'more')}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* No events notice */}
      {records.length === 0 && (
        <div className="text-center text-muted py-4">
          {tval('no-records', 'No records')}
        </div>
      )}
    </div>
  );
};

export default CalendarDisplay;
