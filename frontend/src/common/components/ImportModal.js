import { useState, useMemo, useCallback } from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import ProgressBar from 'react-bootstrap/ProgressBar';
import { IoCloudUploadOutline as ImportIcon } from 'react-icons/io5';

import {
  parseTabularFile, guessMapping, mappableFields, runImport, IMPORT_ACCEPT,
} from '../tools/importer';

/**
 * ImportModal — a file, its columns matched to fields, and the rows written.
 *
 * The runtime half of the file import, in `common/` for the reason the export
 * is: the sandbox mounts it and every generated application's list page mounts
 * the same file, so a spreadsheet that imports in the preview imports in the
 * shipped application **structurally** rather than because two implementations
 * were kept in agreement.
 *
 * It owns no transport. `createRecord` is the host's own create call — the one
 * its form posts through — which is what makes the write role, the model
 * validation, the required check, the write-boundary normalisation, the
 * on-create behaviours and the computed fields all apply with nothing
 * re-implemented here (see `tools/importer/runImport.js`).
 *
 * Four steps, and the middle one is the feature: **pick → map → run → report**.
 * A one-step "upload and it appears" would be an inference nobody checked
 * writing rows nobody reviewed, and the column a spreadsheet calls `Type` is
 * not reliably the field called `kind`.
 */

const _REASONS = {
  'import-no-file': ['import-no-file', 'Choose a file first'],
  'import-format-unknown': ['import-format-unknown', 'That file type cannot be read'],
  'import-read-failed': ['import-read-failed', 'That file could not be opened'],
  'import-empty-file': ['import-empty-file', 'That file has no header row'],
  'import-too-many-rows': ['import-too-many-rows', 'That file has too many rows'],
};

const IGNORE = '';

const ImportModal = ({
  show,
  onHide,
  entityLabel = '',
  fields = [],
  createRecord,
  onDone,
  t,
}) => {
  const tval = useCallback(
    (key, fallback) => (t ? t(key, fallback) : fallback), [t]);

  const [parsed, setParsed] = useState(null);
  const [mapping, setMapping] = useState({});
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);
  const [report, setReport] = useState(null);

  const targets = useMemo(() => mappableFields(fields), [fields]);
  // A required field nobody mapped means every single row will be refused. It
  // is named before the run rather than five thousand times during it.
  const missingRequired = useMemo(() => {
    if (!parsed) return [];
    const mapped = new Set(Object.values(mapping).filter(Boolean));
    return targets.filter((f) => f.required && !mapped.has(f.name));
  }, [parsed, mapping, targets]);

  const reset = () => {
    setParsed(null); setMapping({});
    setError(null); setProgress(null); setReport(null);
  };

  const close = () => { reset(); if (onHide) onHide(); };

  const handleFile = async (event) => {
    const picked = event.target.files && event.target.files[0];
    setError(null); setReport(null); setProgress(null);
    if (!picked) { setParsed(null); return; }

    const result = await parseTabularFile(picked);
    if (!result.ok) {
      const [key, fallback] = _REASONS[result.reason] || _REASONS['import-read-failed'];
      const limit = result.limit ? ` (${result.rows} / ${result.limit})` : '';
      setParsed(null);
      setError(`${tval(key, fallback)}${limit}`);
      return;
    }
    setParsed(result);
    setMapping(guessMapping(result.columns, targets));
  };

  const run = async () => {
    setProgress({ done: 0, total: parsed.rows.length });
    const result = await runImport({
      rows: parsed.rows,
      mapping,
      fields: targets,
      createRecord,
      onProgress: setProgress,
      t,
    });
    setProgress(null);
    setReport(result);
    if (onDone) onDone(result);
  };

  const running = progress !== null;
  const mappedCount = Object.values(mapping).filter(Boolean).length;

  return (
    <Modal show={show} onHide={close} size="lg" centered className="migratis-modal">
      <Modal.Header closeButton>
        <Modal.Title>
          <ImportIcon className="me-2" />
          {tval('import-records', 'Import records')}
          {entityLabel ? ` — ${entityLabel}` : ''}
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {!report && (
          <div className="migratis-field">
            <label className="form-label" htmlFor="import-file">
              {tval('import-choose-file', 'Choose a CSV or Excel file')}
            </label>
            <input
              id="import-file"
              type="file"
              className="form-control"
              accept={IMPORT_ACCEPT}
              disabled={running}
              onChange={handleFile}
            />
            <div className="form-text">
              {tval('import-file-hint',
                'The first row is read as the column names. The file is read in '
                + 'your browser and never uploaded.')}
            </div>
          </div>
        )}

        {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}

        {parsed && !report && (
          <>
            <p className="form-intro mt-3">
              {`${parsed.columns.length} ${tval('import-columns', 'columns')} · `}
              {`${parsed.rows.length} ${tval('import-rows', 'rows')}`}
              {parsed.sheetName ? ` · ${parsed.sheetName}` : ''}
            </p>

            <table className="table table-sm align-middle">
              <thead>
                <tr>
                  <th>{tval('import-file-column', 'Column in the file')}</th>
                  <th>{tval('import-example', 'Example')}</th>
                  <th>{tval('import-target-field', 'Field')}</th>
                </tr>
              </thead>
              <tbody>
                {parsed.columns.map((column, index) => (
                  <tr key={`${column}-${index}`}>
                    <td>{column || <em>{tval('import-unnamed-column', 'unnamed')}</em>}</td>
                    <td className="text-muted text-truncate" style={{ maxWidth: '14rem' }}>
                      {(parsed.rows.find((r) => String(r[index] ?? '').trim()) || [])[index] || ''}
                    </td>
                    <td>
                      <select
                        className="form-select form-select-sm"
                        aria-label={column || `column ${index + 1}`}
                        disabled={running}
                        value={mapping[index] || IGNORE}
                        onChange={(e) => setMapping(
                          { ...mapping, [index]: e.target.value })}
                      >
                        <option value={IGNORE}>
                          {tval('import-ignore-column', '— do not import —')}
                        </option>
                        {targets.map((field) => (
                          <option
                            key={field.name}
                            value={field.name}
                            disabled={Object.entries(mapping).some(
                              ([k, v]) => v === field.name && Number(k) !== index)}
                          >
                            {field.description || field.name}
                            {field.required ? ' *' : ''}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!!missingRequired.length && (
              <div className="alert alert-warning mb-0">
                {tval('import-missing-required',
                  'Every row would be refused: these fields are required and no '
                  + 'column feeds them')}
                {': '}
                {missingRequired.map((f) => f.description || f.name).join(', ')}
              </div>
            )}
          </>
        )}

        {running && (
          <div className="mt-3">
            <ProgressBar
              now={progress.total ? (progress.done / progress.total) * 100 : 0}
              label={`${progress.done} / ${progress.total}`}
            />
          </div>
        )}

        {report && (
          <div className="mt-2">
            <p className="mb-2">
              <strong>{report.created}</strong>
              {' '}
              {tval('import-records-created', 'records created')}
              {report.failed.length
                ? ` · ${report.failed.length} ${tval('import-rows-refused', 'rows refused')}`
                : ''}
            </p>
            {report.stopped && (
              <div className="alert alert-warning">
                {tval('import-stopped-early',
                  'The import stopped: too many rows in a row were refused for the '
                  + 'same reason. Fix the mapping or the file and try again.')}
              </div>
            )}
            {!!report.failed.length && (
              <table className="table table-sm">
                <thead>
                  <tr>
                    <th>{tval('import-line', 'Line')}</th>
                    <th>{tval('import-reason', 'Reason')}</th>
                  </tr>
                </thead>
                <tbody>
                  {report.failed.slice(0, 50).map((failure) => (
                    <tr key={failure.row}>
                      <td>{failure.line}</td>
                      <td>{failure.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={close} disabled={running}>
          {report ? tval('close', 'Close') : tval('cancel', 'Cancel')}
        </Button>
        {!report && (
          <Button
            variant="primary"
            onClick={run}
            disabled={running || !parsed || !mappedCount || !!missingRequired.length}
          >
            {running
              ? tval('importing', 'Importing…')
              : `${tval('import', 'Import')}${parsed ? ` (${parsed.rows.length})` : ''}`}
          </Button>
        )}
      </Modal.Footer>
    </Modal>
  );
};

export default ImportModal;
