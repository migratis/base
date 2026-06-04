import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TableDisplay from './TableDisplay';

// Regression: TableDisplay used to render only edit/delete icons per row and
// never surfaced the entity's workflow-step buttons, even though every other
// piece of the sandbox pipeline (SandboxList → DisplayModeFactory) forwards
// `onInteraction`, `viewAs`, `getRoleRank`. Multi-purpose store symptom: the
// admin opened the Payment table and saw no "Confirm paid" / "Mark failed" /
// "Start refund" buttons — making it impossible to advance the bank-transfer
// flow even though the workflow step config was correct. These tests pin the
// contract that TableDisplay applies `getVisibleInteractions` per row and
// renders the surviving buttons.

const _baseEntity = {
  name: 'Payment',
  fields: [
    { name: 'amount',         field_type: 'decimal' },
    { name: 'status',         field_type: 'string' },
    { name: 'payment_method', field_type: 'string' },
  ],
  relationships: [],
};

const _config = {
  interactions: [
    {
      step_id: 200,
      trigger: 'Confirm paid',
      trigger_label: 'Confirm paid',
      action: 'update',
      mode: 'direct_create',
      actor_role: 'admin',
      precondition: { op: 'equals', field: 'status', scope: 'source', value: 'pending' },
      completion:   { op: 'equals', field: 'status', value: 'paid' },
      prereq_step_ids: [],
      entity_min_write_role: 'customer',
    },
    {
      step_id: 201,
      trigger: 'Mark failed',
      trigger_label: 'Mark failed',
      action: 'update',
      mode: 'direct_create',
      actor_role: 'admin',
      precondition: { op: 'equals', field: 'status', scope: 'source', value: 'pending' },
      completion:   { op: 'equals', field: 'status', value: 'failed' },
      prereq_step_ids: [],
      entity_min_write_role: 'customer',
    },
    {
      step_id: 207,
      trigger: 'Start refund',
      trigger_label: 'Start refund',
      action: 'create',
      mode: 'form',
      target: 'Refund',
      link_via: 'payment',
      actor_role: 'admin',
      precondition: { op: 'equals', field: 'status', scope: 'source', value: 'paid' },
      completion:   { op: 'equals', field: 'status', value: 'pending' },
      prereq_step_ids: [],
      entity_min_write_role: 'customer',
    },
  ],
};

const _records = [
  { id: 1, data: { amount: '100', status: 'pending', payment_method: 'bank_transfer' } },
  { id: 2, data: { amount: '200', status: 'paid',    payment_method: 'credit_card' } },
];

const _getRoleRank = (name) => ({ public: 0, customer: 1, admin: 2 }[name] ?? null);

describe('TableDisplay — workflow interaction buttons per row', () => {
  test('admin sees Confirm paid + Mark failed on a pending payment row', () => {
    render(
      <TableDisplay
        entity={_baseEntity}
        records={[_records[0]]}
        config={_config}
        onInteraction={jest.fn()}
        viewAs="admin"
        getRoleRank={_getRoleRank}
      />
    );
    expect(screen.getByRole('button', { name: 'Confirm paid' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Mark failed' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start refund' })).not.toBeInTheDocument();
  });

  test('admin sees Start refund on a paid payment row but not Confirm paid', () => {
    render(
      <TableDisplay
        entity={_baseEntity}
        records={[_records[1]]}
        config={_config}
        onInteraction={jest.fn()}
        viewAs="admin"
        getRoleRank={_getRoleRank}
      />
    );
    expect(screen.getByRole('button', { name: 'Start refund' })).toBeInTheDocument();
    // Confirm paid is hidden because precondition status='pending' doesn't match,
    // AND because status='paid' satisfies the completion predicate.
    expect(screen.queryByRole('button', { name: 'Confirm paid' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Mark failed' })).not.toBeInTheDocument();
  });

  test('customer never sees admin-only interactions even when preconditions match', () => {
    render(
      <TableDisplay
        entity={_baseEntity}
        records={_records}
        config={_config}
        onInteraction={jest.fn()}
        viewAs="customer"
        getRoleRank={_getRoleRank}
      />
    );
    expect(screen.queryByRole('button', { name: 'Confirm paid' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Mark failed' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start refund' })).not.toBeInTheDocument();
  });

  test('clicking an interaction button calls onInteraction with the row prefill', () => {
    const onInteraction = jest.fn();
    render(
      <TableDisplay
        entity={_baseEntity}
        records={[_records[1]]}
        config={_config}
        onInteraction={onInteraction}
        viewAs="admin"
        getRoleRank={_getRoleRank}
      />
    );
    screen.getByRole('button', { name: 'Start refund' }).click();
    expect(onInteraction).toHaveBeenCalledTimes(1);
    const [target, prefill, mode] = onInteraction.mock.calls[0];
    expect(target).toBe('Refund');
    expect(mode).toBe('form');
    // The row's id flows through as both __source_id and the link_via FK.
    expect(prefill.__source_id).toBe(2);
    expect(prefill.payment).toBe(2);
    expect(prefill.__step_id).toBe(207);
  });

  test('an entity with no interactions renders no actions and no extra header', () => {
    render(
      <TableDisplay
        entity={_baseEntity}
        records={_records}
        config={{ interactions: [] }}
        onInteraction={jest.fn()}
        viewAs="admin"
        getRoleRank={_getRoleRank}
      />
    );
    expect(screen.queryByRole('button', { name: /confirm|mark|refund/i })).not.toBeInTheDocument();
  });

  test('omitting onInteraction suppresses the buttons (parent opted out)', () => {
    render(
      <TableDisplay
        entity={_baseEntity}
        records={[_records[0]]}
        config={_config}
        viewAs="admin"
        getRoleRank={_getRoleRank}
      />
    );
    expect(screen.queryByRole('button', { name: 'Confirm paid' })).not.toBeInTheDocument();
  });
});
