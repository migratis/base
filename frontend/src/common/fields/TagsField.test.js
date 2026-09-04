/**
 * A tags editor is handed whatever the column holds, and the column is JSON.
 *
 * `render_as: 'tags'` is a *display* choice over an ordinary `string` field, so
 * nothing anywhere guarantees the value is a list. It arrives as a string from
 * an external lookup (prod app 8's `Title.genres`, filled from OMDb's
 * `"Genre": "Action, Adventure, Sci-Fi"`), from a seeded row, from an agent
 * write, and from every row that already existed when someone switched
 * `render_as` from `input` to `tags`. TagsField did `watch(name) || []` and then
 * `value.map(...)`, so any of those blanked the page with
 * `TypeError: p.map is not a function` behind the error boundary.
 *
 * Same shape as the geo and numeric bugs: **the reader tolerates, and the value
 * is normalised** — rendering the string as tags while the form still submits
 * the string would leave one column holding two shapes, which is prod app 6's
 * `"197.8"` all over again.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { useForm, FormProvider } from 'react-hook-form';
import TagsField from './TagsField';

const Harness = ({ initial, onValues }) => {
  const methods = useForm({ defaultValues: { genres: initial } });
  if (onValues) onValues(methods.getValues);
  return (
    <FormProvider {...methods}>
      <TagsField name="genres" label="Genres" />
    </FormProvider>
  );
};

describe('TagsField tolerates whatever the column holds', () => {
  test('a comma-separated string renders as tags instead of crashing', () => {
    render(<Harness initial="Action, Adventure, Sci-Fi" />);
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Adventure')).toBeInTheDocument();
    expect(screen.getByText('Sci-Fi')).toBeInTheDocument();
  });

  test('and the form value becomes the array, so the row stores one shape', async () => {
    let getValues;
    render(<Harness initial="Action, Adventure" onValues={(g) => { getValues = g; }} />);
    await waitFor(() => {
      expect(getValues().genres).toEqual(['Action', 'Adventure']);
    });
  });

  test('a single bare string is one tag, not a character list', () => {
    render(<Harness initial="Documentary" />);
    expect(screen.getByText('Documentary')).toBeInTheDocument();
  });

  test('an array is left exactly as it is', () => {
    render(<Harness initial={['Drama', 'Comedy']} />);
    expect(screen.getByText('Drama')).toBeInTheDocument();
    expect(screen.getByText('Comedy')).toBeInTheDocument();
  });

  test('null, a number and an object are empty rather than fatal', () => {
    // Never a guess: a shape with no reading is no tags, and the user adds
    // their own. Rendering `[object Object]` as a tag would be worse.
    expect(() => render(<Harness initial={null} />)).not.toThrow();
    expect(() => render(<Harness initial={7} />)).not.toThrow();
    expect(() => render(<Harness initial={{ a: 1 }} />)).not.toThrow();
  });

  test('empty segments are dropped, so a trailing comma is not a blank tag', async () => {
    let getValues;
    render(<Harness initial="Action, , Drama," onValues={(g) => { getValues = g; }} />);
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Drama')).toBeInTheDocument();
    await waitFor(() => expect(getValues().genres).toEqual(['Action', 'Drama']));
  });

  test('typing still adds a tag on top of a normalised string', async () => {
    render(<Harness initial="Action" />);
    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'Thriller{enter}');
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Thriller')).toBeInTheDocument();
  });
});
