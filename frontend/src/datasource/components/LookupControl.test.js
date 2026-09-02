import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { FormProvider, useForm } from 'react-hook-form';
import '@testing-library/jest-dom';

/**
 * SCOPE_external_data_sources.md@d2de531 P4 — the runtime surface, and §8.4's
 * three failures rendered honestly.
 *
 * The rail this file exists for: **a failure is never an empty result list.**
 * An empty list that actually means *you have run out* is the
 * `route-not-found`-vs-`routing-engine-unavailable` mistake in a new module, and
 * it is invisible until someone's key expires.
 */

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k) => k }),
}));

jest.mock('../../common/tools/axios', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

const LookupControl = require('./LookupControl').default;

const SOURCES = [{ id: 4, label: 'TMDB', fields: ['titre', 'resume'], two_step: false }];

const Harness = ({ transport, sources = SOURCES, onValues }) => {
  const methods = useForm({ defaultValues: { titre: '', resume: '' } });
  onValues && onValues(methods);
  return (
    <FormProvider {...methods}>
      <LookupControl sources={sources} transport={transport} t={(k) => k} />
      <input aria-label="titre" {...methods.register('titre')} />
      <input aria-label="resume" {...methods.register('resume')} />
    </FormProvider>
  );
};

const transportOf = (search, detail = jest.fn()) => ({ search, detail });

const openAndSearch = async (text = 'dune') => {
  fireEvent.click(screen.getByText('TMDB'));
  fireEvent.change(screen.getByLabelText('TMDB'), { target: { value: text } });
  fireEvent.click(screen.getByText('datasource-search'));
};

it('renders nothing at all when the entity declares no source', () => {
  render(<Harness sources={[]} transport={transportOf(jest.fn())} />);
  expect(screen.queryByTestId('lookup-control')).not.toBeInTheDocument();
});

it('fills the form from a picked candidate, and writes nothing itself', async () => {
  const search = jest.fn().mockResolvedValue({
    ok: true, candidates: [{ label: 'Dune', id: '1',
                             values: { titre: 'Dune', resume: 'Paul Atreides' } }],
  });
  render(<Harness transport={transportOf(search)} />);
  await openAndSearch();
  fireEvent.click(await screen.findByText('datasource-use-this'));
  await waitFor(() => expect(screen.getByLabelText('titre')).toHaveValue('Dune'));
  expect(screen.getByLabelText('resume')).toHaveValue('Paul Atreides');
});

it('leaves the picked values editable — a suggestion is a suggestion', async () => {
  const search = jest.fn().mockResolvedValue({
    ok: true, candidates: [{ label: 'Dune', id: '1', values: { titre: 'Dune' } }],
  });
  render(<Harness transport={transportOf(search)} />);
  await openAndSearch();
  fireEvent.click(await screen.findByText('datasource-use-this'));
  await waitFor(() => expect(screen.getByLabelText('titre')).toHaveValue('Dune'));
  fireEvent.change(screen.getByLabelText('titre'), { target: { value: 'Dune (1984)' } });
  expect(screen.getByLabelText('titre')).toHaveValue('Dune (1984)');
});

describe('the three failures are told apart, and none of them is an empty list', () => {
  it('an unreachable source keeps what the user typed and says so', async () => {
    const search = jest.fn().mockResolvedValue({
      ok: false, key: 'datasource-unavailable', candidates: [] });
    render(<Harness transport={transportOf(search)} />);
    await openAndSearch();
    expect(await screen.findByTestId('lookup-failure'))
      .toHaveTextContent('datasource-unavailable');
    expect(screen.queryByTestId('lookup-empty')).not.toBeInTheDocument();
    expect(screen.getByLabelText('TMDB')).toHaveValue('dune');
  });

  it('a refusal names the status the source answered', async () => {
    const search = jest.fn().mockResolvedValue({
      ok: false, key: 'datasource-refused', sourceStatus: 401, candidates: [] });
    render(<Harness transport={transportOf(search)} />);
    await openAndSearch();
    expect(await screen.findByTestId('lookup-failure')).toHaveTextContent('401');
  });

  it('an exhausted quota is said in those words', async () => {
    const search = jest.fn().mockResolvedValue({
      ok: false, key: 'datasource-quota-exhausted', candidates: [] });
    render(<Harness transport={transportOf(search)} />);
    await openAndSearch();
    expect(await screen.findByTestId('lookup-failure'))
      .toHaveTextContent('datasource-quota-exhausted');
  });

  it('a source with nothing matching is a real answer, and reads as one', async () => {
    const search = jest.fn().mockResolvedValue({ ok: true, candidates: [] });
    render(<Harness transport={transportOf(search)} />);
    await openAndSearch();
    expect(await screen.findByTestId('lookup-empty')).toBeInTheDocument();
    expect(screen.queryByTestId('lookup-failure')).not.toBeInTheDocument();
  });
});

describe('the two-step flow', () => {
  it('fires the second request on the pick, not on the search', async () => {
    const search = jest.fn().mockResolvedValue({
      ok: true, needsDetail: true,
      candidates: [{ label: 'Dune', id: '438631', values: { titre: 'Dune' } }],
    });
    const detail = jest.fn().mockResolvedValue({
      ok: true, values: { titre: 'Dune', resume: 'Full synopsis' } });
    render(<Harness sources={[{ ...SOURCES[0], two_step: true }]}
                    transport={transportOf(search, detail)} />);
    await openAndSearch();
    expect(detail).not.toHaveBeenCalled();
    fireEvent.click(await screen.findByText('datasource-use-this'));
    await waitFor(() => expect(detail).toHaveBeenCalledWith(4, '438631'));
    await waitFor(() => expect(screen.getByLabelText('resume'))
      .toHaveValue('Full synopsis'));
  });

  it('leaves the form untouched when the second request fails', async () => {
    /* Filling from the thinner search result would look like success. */
    const search = jest.fn().mockResolvedValue({
      ok: true, candidates: [{ label: 'Dune', id: '1', values: { titre: 'Dune' } }] });
    const detail = jest.fn().mockResolvedValue({
      ok: false, key: 'datasource-unavailable' });
    render(<Harness sources={[{ ...SOURCES[0], two_step: true }]}
                    transport={transportOf(search, detail)} />);
    await openAndSearch();
    fireEvent.click(await screen.findByText('datasource-use-this'));
    expect(await screen.findByTestId('lookup-failure')).toBeInTheDocument();
    expect(screen.getByLabelText('titre')).toHaveValue('');
  });
});

it('never spends a call on a blank search', async () => {
  const search = jest.fn();
  render(<Harness transport={transportOf(search)} />);
  fireEvent.click(screen.getByText('TMDB'));
  fireEvent.click(screen.getByText('datasource-search'));
  expect(search).not.toHaveBeenCalled();
});

it('renders the payload as text, never as markup (D10)', async () => {
  const search = jest.fn().mockResolvedValue({
    ok: true, candidates: [{ label: '<img src=x onerror=alert(1)>', id: '1',
                             values: { titre: 'x' } }] });
  render(<Harness transport={transportOf(search)} />);
  await openAndSearch();
  const list = await screen.findByTestId('lookup-candidates');
  expect(list.querySelector('img')).toBeNull();
  expect(list).toHaveTextContent('<img src=x onerror=alert(1)>');
});
