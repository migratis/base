import React from 'react';
import { render, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PaginatedEntitySelectField from './PaginatedEntitySelectField';
import CommonService from '../services/common.service';

// GAP_ANALYSIS_agent_lane_poc.md §5 — the relationship "to entity" selector
// listed entities from ALL the user's applications because this field never
// forwarded an application filter. It must pass extraParams through to the
// entity list call so the dropdown is scoped to the current application.

jest.mock('./SelectField', () => () => <div data-testid="select" />);
jest.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k) => k }),
}));
jest.mock('react-router-dom', () => ({ useNavigate: () => jest.fn() }), { virtual: true });
jest.mock('../services/common.service', () => ({
  __esModule: true,
  default: { getEntities: jest.fn(() => Promise.resolve({ items: [], count: 0 })) },
}));

describe('PaginatedEntitySelectField', () => {
  beforeEach(() => jest.clearAllMocks());

  test('forwards extraParams (application scope) to the entity list call', async () => {
    render(
      <PaginatedEntitySelectField
        app="generator"
        entity="entity"
        status="active"
        name="rel.to_entity"
        extraParams={{ application: 7 }}
      />,
    );
    await waitFor(() => expect(CommonService.getEntities).toHaveBeenCalled());
    expect(CommonService.getEntities).toHaveBeenCalledWith(
      'generator', 'entity', 'active', '', 1, { application: 7 },
    );
  });

  test('defaults extraParams to {} when none is given (back-compat)', async () => {
    render(
      <PaginatedEntitySelectField
        app="generator" entity="entity" status="active" name="rel.to_entity"
      />,
    );
    await waitFor(() => expect(CommonService.getEntities).toHaveBeenCalled());
    expect(CommonService.getEntities).toHaveBeenCalledWith(
      'generator', 'entity', 'active', '', 1, {},
    );
  });
});
