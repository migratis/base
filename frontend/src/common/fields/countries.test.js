import { COUNTRIES } from './countries';

describe('COUNTRIES — ISO 3166-1 country list', () => {
  test('contains at least 200 entries', () => {
    expect(COUNTRIES.length).toBeGreaterThanOrEqual(200);
  });

  test('every entry has a 2-letter alpha-2 value and a non-empty label', () => {
    for (const c of COUNTRIES) {
      expect(c.value).toMatch(/^[A-Z]{2}$/);
      expect(typeof c.label).toBe('string');
      expect(c.label.length).toBeGreaterThan(0);
    }
  });

  test('contains the well-known anchor entries used by tests/people', () => {
    const codes = COUNTRIES.map((c) => c.value);
    // Anchor set — if any of these go missing the list almost certainly
    // got truncated.
    for (const code of ['FR', 'DE', 'US', 'GB', 'CA', 'JP', 'RO', 'BR', 'AU']) {
      expect(codes).toContain(code);
    }
  });

  test('codes are unique', () => {
    const codes = COUNTRIES.map((c) => c.value);
    expect(new Set(codes).size).toBe(codes.length);
  });
});
