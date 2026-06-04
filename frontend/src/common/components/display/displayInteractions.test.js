// Parametric smoke tests: every built-in display mode must surface the
// per-row workflow buttons that `getVisibleInteractions` returns. The full
// visibility-rule coverage lives in interactionVisibility.test.js; here we
// only confirm each display wires up the `InteractionRowActions` helper for
// its records — i.e. that the same Payment regression we caught in the
// Table mode doesn't recur in List / Kanban / Masonry / Gallery / Calendar
// / Grid. Each block also asserts the negative case (no admin button when
// viewer is the customer) to confirm Stage B gating reaches the row.

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

import TableDisplay    from './TableDisplay';
import CardsDisplay    from './CardsDisplay';
import ListDisplay     from './ListDisplay';
import KanbanDisplay   from './KanbanDisplay';
import MasonryDisplay  from './MasonryDisplay';
import GalleryDisplay  from './GalleryDisplay';
import CalendarDisplay from './CalendarDisplay';
import GridDisplay     from './GridDisplay';

const _interactions = [
  {
    step_id: 200,
    trigger_label: 'Confirm paid',
    action: 'update', mode: 'direct_create',
    actor_role: 'admin',
    precondition: { op: 'equals', field: 'status', scope: 'source', value: 'pending' },
    completion:   { op: 'equals', field: 'status', value: 'paid' },
    prereq_step_ids: [],
    entity_min_write_role: 'customer',
  },
];

const _entity = {
  name: 'Payment',
  fields: [
    { name: 'name',           field_type: 'string' },
    { name: 'status',         field_type: 'string' },
    { name: 'amount',         field_type: 'decimal' },
    // Calendar needs a date-ish field to compute eventsByDay
    { name: 'created_at',     field_type: 'datetime' },
  ],
  relationships: [],
};

const _records = [
  {
    id: 1,
    data: {
      name: 'PMT-0001',
      status: 'pending',
      amount: '100',
      // ISO date so CalendarDisplay parseDate succeeds
      created_at: new Date().toISOString(),
    },
  },
];

const _baseProps = {
  entity: _entity,
  records: _records,
  config: { interactions: _interactions },
  onEdit: jest.fn(),
  onDelete: jest.fn(),
  onInteraction: jest.fn(),
  viewAs: 'admin',
  getRoleRank: (n) => ({ public: 0, customer: 1, admin: 2 }[n] ?? null),
  t: (k, fb) => fb || k,
};

const _adminCases = [
  { name: 'TableDisplay',    Component: TableDisplay,    requiresHover: false },
  { name: 'CardsDisplay',    Component: CardsDisplay,    requiresHover: false },
  { name: 'ListDisplay',     Component: ListDisplay,     requiresHover: false },
  { name: 'KanbanDisplay',   Component: KanbanDisplay,   requiresHover: false },
  { name: 'MasonryDisplay',  Component: MasonryDisplay,  requiresHover: false },
  { name: 'GalleryDisplay',  Component: GalleryDisplay,  requiresHover: false },
  { name: 'CalendarDisplay', Component: CalendarDisplay, requiresHover: false },
  // GridDisplay only reveals the actions overlay on hover. We assert the
  // hover-visible path by simulating mouseEnter on the cell rather than
  // looking for the button at first render.
  { name: 'GridDisplay',     Component: GridDisplay,     requiresHover: true  },
];

describe('All built-in display modes surface workflow buttons per row', () => {
  _adminCases.filter((c) => !c.requiresHover).forEach(({ name, Component }) => {
    test(`${name}: admin sees Confirm paid on a pending row`, () => {
      render(<Component {..._baseProps} />);
      expect(screen.getByRole('button', { name: 'Confirm paid' })).toBeInTheDocument();
    });

    test(`${name}: customer never sees admin-only Confirm paid`, () => {
      render(<Component {..._baseProps} viewAs="customer" />);
      expect(screen.queryByRole('button', { name: 'Confirm paid' })).not.toBeInTheDocument();
    });
  });

  test('GridDisplay: admin sees Confirm paid on the hover-revealed overlay', () => {
    // GridCell's actions overlay is gated on hover (onMouseEnter). The cell
    // wrapper carries a positioned outer container per record — fire the
    // React synthetic mouseEnter on it. dispatchEvent('mouseover') does NOT
    // trigger React's onMouseEnter reliably under jsdom.
    const { container } = render(<GridDisplay {..._baseProps} />);
    // Cell wrappers are the only divs with cursor:pointer inline style.
    const cellHosts = Array.from(container.querySelectorAll('div'))
      .filter((d) => d.style.cursor === 'pointer');
    expect(cellHosts.length).toBeGreaterThan(0);
    fireEvent.mouseEnter(cellHosts[0]);
    expect(screen.getByRole('button', { name: 'Confirm paid' })).toBeInTheDocument();
  });
});
