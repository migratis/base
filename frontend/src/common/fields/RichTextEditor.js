import { useEffect, useRef } from "react";
import { useTranslation } from 'react-i18next';
import { useFormContext } from "react-hook-form";

// Lightweight dependency-free rich-text field. Renders a contentEditable area
// with a small formatting toolbar and stores the resulting HTML in the form
// value. Matches the react-hook-form field contract used across common/fields
// (name, label, help, required, …) so it is a drop-in for generated forms that
// request render_as='rich_text'.
const TOOLBAR = [
  { cmd: 'bold',                 label: 'B', style: { fontWeight: 'bold' } },
  { cmd: 'italic',               label: 'I', style: { fontStyle: 'italic' } },
  { cmd: 'underline',            label: 'U', style: { textDecoration: 'underline' } },
  { cmd: 'insertUnorderedList',  label: '• List', style: {} },
  { cmd: 'insertOrderedList',    label: '1. List', style: {} },
];

// Tags/attributes the editor itself produces and that are safe to render.
const ALLOWED_TAGS = new Set([
  'B', 'STRONG', 'I', 'EM', 'U', 'P', 'BR', 'UL', 'OL', 'LI',
  'SPAN', 'DIV', 'A', 'H1', 'H2', 'H3', 'BLOCKQUOTE',
]);
// Allow-list anchor hrefs by scheme. A deny-list is bypassable (browsers strip
// embedded control chars/whitespace before resolving the scheme), so resolve
// with the URL parser — which performs that normalization — and permit only
// http/https/mailto and relative URLs (which resolve to http/https).
function isSafeHref(value) {
  try {
    const { protocol } = new URL(value, document.baseURI);
    return protocol === 'http:' || protocol === 'https:' || protocol === 'mailto:';
  } catch {
    return false;
  }
}

// Dependency-free whitelist sanitizer. The stored value is rendered via
// innerHTML, so untrusted markup (e.g. a description authored by another user)
// could otherwise inject script/handlers — strip anything not on the allow
// list. NOTE: this is a conservative fallback; prefer DOMPurify if a sanitizer
// dependency becomes available.
function sanitizeHtml(dirty) {
  // <template> content is inert: assigning innerHTML neither runs scripts nor
  // loads resources, so parsing here is safe.
  const tpl = document.createElement('template');
  tpl.innerHTML = String(dirty);
  tpl.content.querySelectorAll('*').forEach((el) => {
    if (!ALLOWED_TAGS.has(el.tagName)) {
      el.remove();
      return;
    }
    [...el.attributes].forEach((attr) => {
      const isHref = el.tagName === 'A' && attr.name.toLowerCase() === 'href';
      // Keep only safe (http/https/mailto/relative) hrefs on anchors; strip
      // everything else (on*, style, unsafe schemes, …).
      if (isHref && isSafeHref(attr.value)) return;
      el.removeAttribute(attr.name);
    });
  });
  return tpl.innerHTML;
}

export default function RichTextEditor({
  name,
  label,
  help = null,
  required = false,
  disabled = false,
  placeholder = '',
  isVisible = true,
  serverError = false,
}) {
  const { t } = useTranslation('form');
  const { register, setValue, watch, formState: { errors } } = useFormContext();
  const editorRef = useRef(null);

  const getNestedError = (errs, path) => path.split('.').reduce((acc, key) => acc?.[key], errs);
  const error = getNestedError(errors, name) || serverError;

  const value = watch(name);

  // Register the field for validation (the editable area is not a native input,
  // so the value is pushed via setValue rather than a ref).
  useEffect(() => {
    register(name, { required, shouldUnregister: true });
  }, [register, name, required]);

  // Hide → clear, matching the other fields' isVisible behaviour.
  useEffect(() => {
    if (!isVisible) setValue(name, null);
  }, [isVisible, name, setValue]);

  // Sync external value changes (e.g. form reset / edit) into the DOM without
  // disturbing the caret while the user is typing.
  useEffect(() => {
    const el = editorRef.current;
    if (!el) return;
    const html = value == null ? '' : sanitizeHtml(String(value));
    if (document.activeElement !== el && el.innerHTML !== html) {
      el.innerHTML = html;
    }
  }, [value]);

  const pushValue = () => {
    const html = editorRef.current?.innerHTML ?? '';
    // Treat an empty editor (browsers leave <br>) as empty for `required`.
    const isEmpty = html === '' || html === '<br>';
    setValue(name, isEmpty ? '' : html, { shouldValidate: true, shouldDirty: true });
  };

  const exec = (cmd) => {
    if (disabled) return;
    editorRef.current?.focus();
    document.execCommand(cmd, false, null);
    pushValue();
  };

  if (!isVisible) return null;

  return (
    <div className="migratis-field">
      <label className={error ? 'text-danger' : ''}>
        {label}
        {required ? <span style={{ color: 'red' }}>&nbsp;*</span> : ''}
      </label>

      {help && <small className="form-text text-muted">{help}</small>}

      {!disabled && (
        <div className="btn-group btn-group-sm mb-1 d-flex" role="toolbar">
          {TOOLBAR.map((b) => (
            <button
              key={b.cmd}
              type="button"
              className="btn btn-outline-secondary"
              style={b.style}
              // Use onMouseDown + preventDefault so the editor keeps its
              // selection/focus when the toolbar button is pressed.
              onMouseDown={(e) => { e.preventDefault(); exec(b.cmd); }}
              aria-label={b.cmd}
            >
              {b.label}
            </button>
          ))}
        </div>
      )}

      <div
        ref={editorRef}
        contentEditable={!disabled}
        suppressContentEditableWarning
        onInput={pushValue}
        onBlur={pushValue}
        data-placeholder={placeholder}
        className={`form-control ${error ? 'is-invalid' : ''}`}
        style={{ minHeight: '8rem', overflowY: 'auto', textAlign: 'left' }}
        role="textbox"
        aria-multiline="true"
        aria-label={label}
      />

      <small className="form-text text-danger">
        {!error?.type && error}
        {error?.type === 'required' && t('empty-field')}
      </small>
    </div>
  );
}
