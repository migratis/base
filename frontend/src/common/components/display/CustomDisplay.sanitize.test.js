import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import CustomDisplay from './CustomDisplay';

// The sandbox compiler must inject `sanitizeHtml` into the compiled component's
// scope (mirroring the generated app), so an AI display that routes rich text
// through it renders sanitized markup instead of throwing (→ fallback).
function renderWith(code, componentName) {
  const sandboxConfig = { _custom_components: { [componentName]: code } };
  const entityConfig = {
    display_mode_options: { custom_display: { name: componentName } },
  };
  const Fallback = () => <div data-testid="fallback">fallback</div>;
  return render(
    <CustomDisplay
      records={[{ id: 1, data: { desc: '<b>safe</b><img src=x onerror=alert(1)>' } }]}
      entityConfig={entityConfig}
      sandboxConfig={sandboxConfig}
      FallbackDisplay={Fallback}
      t={(k) => k}
    />,
  );
}

describe('CustomDisplay — sanitizeHtml in compile scope', () => {
  test('component using sanitizeHtml compiles and renders sanitized HTML', () => {
    const name = 'RichDisplay';
    const code =
      "function RichDisplay({ records }) {" +
      "  return React.createElement('div', { 'data-testid': 'rich'," +
      "    dangerouslySetInnerHTML: { __html: sanitizeHtml(records[0].data.desc) } });" +
      "}";
    renderWith(code, name);

    // Did NOT fall back → sanitizeHtml resolved in scope.
    expect(screen.queryByTestId('fallback')).not.toBeInTheDocument();
    const el = screen.getByTestId('rich');
    // Benign markup kept, dangerous handler stripped.
    expect(el.innerHTML).toMatch(/<b>safe<\/b>/);
    expect(el.innerHTML).not.toMatch(/onerror/i);
  });
});
