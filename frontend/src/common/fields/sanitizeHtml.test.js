import { sanitizeHtml } from './sanitizeHtml';

describe('sanitizeHtml — XSS guard for AI custom components', () => {
  test('strips event-handler attributes (onerror, …)', () => {
    const out = sanitizeHtml('<img src=x onerror=alert(1)>');
    expect(out).not.toMatch(/onerror/i);
    expect(out).not.toMatch(/alert\(1\)/);
  });

  test('strips <script> tags', () => {
    const out = sanitizeHtml('<div>hi</div><script>alert(1)</script>');
    expect(out).not.toMatch(/<script/i);
    expect(out).not.toMatch(/alert\(1\)/);
  });

  test('keeps benign formatting tags', () => {
    const out = sanitizeHtml('<b>bold</b> <i>italic</i> <a href="https://x.io">link</a>');
    expect(out).toMatch(/<b>bold<\/b>/);
    expect(out).toMatch(/<i>italic<\/i>/);
    expect(out).toMatch(/<a[^>]*href="https:\/\/x\.io"/);
  });

  test('coerces non-string / nullish input without throwing', () => {
    expect(sanitizeHtml(null)).toBe('');
    expect(sanitizeHtml(undefined)).toBe('');
    expect(sanitizeHtml(42)).toBe('42');
  });
});
