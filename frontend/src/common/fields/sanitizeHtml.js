import DOMPurify from 'dompurify';

// Shared HTML sanitizer for AI-generated custom components. Record/field data
// is attacker-influenced, so any value rendered via dangerouslySetInnerHTML
// MUST pass through here first. DOMPurify drops <script>, event handlers
// (onerror, onclick, …) and unsafe URL schemes while keeping benign formatting
// tags (<b>, <i>, <a href>, …). Injected into the custom-component compile
// scope so AI code can call `sanitizeHtml(...)` without an import.
export function sanitizeHtml(dirty) {
  return DOMPurify.sanitize(String(dirty == null ? '' : dirty));
}

export default sanitizeHtml;
