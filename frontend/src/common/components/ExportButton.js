import { useState } from 'react';
import Dropdown from 'react-bootstrap/Dropdown';
import Spinner from 'react-bootstrap/Spinner';
import { toast } from 'react-toastify';
import { IoDownloadOutline as ExportIcon } from 'react-icons/io5';

/**
 * ExportButton — one control, the formats inside it.
 *
 * One control rather than two or three buttons because the bars this lands in
 * are already full: the sandbox's per-entity toolbar carries five, and it is
 * documented as having had to survive a phone once already.
 *
 * It owns the REPORTING as well as the click. `exportData` never throws and
 * never rejects — a caller in an onClick handler would turn that into an
 * unhandled rejection with nothing on screen — so every outcome comes back as
 * `{ok, reason}` and is said out loud here, in one place, so that every mount
 * words a refusal the same way. A refusal is always shown: the failure mode
 * this replaces is a click that produces no file and no explanation.
 */

// A reason from `exportData` / `useTableExport`, and how it reads. Every key is
// seeded; the fallback is what a namespace that has not been seeded yet shows.
const _REASONS = {
  'export-too-many-rows':    ['export-too-many-rows',    'Too many rows to export'],
  'export-nothing-to-export': ['export-nothing-to-export', 'There is nothing to export'],
  'export-fetch-failed':     ['export-fetch-failed',     'Could not load the rows to export'],
  'export-pdf-unavailable':  ['export-pdf-unavailable',  'PDF export is not available'],
  'export-format-unknown':   ['export-failed',           'Export failed'],
  'export-failed':           ['export-failed',           'Export failed'],
};

const ExportButton = ({
  onExport,
  formats = ['xlsx', 'csv'],
  busy = false,
  disabled = false,
  size = 'sm',
  variant = 'outline-secondary',
  align = 'end',
  t,
}) => {
  const [running, setRunning] = useState(false);
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback);

  if (!formats.length) return null;

  const labels = {
    xlsx: tval('export-excel', 'Excel'),
    csv:  tval('export-csv', 'CSV'),
    pdf:  tval('export-pdf', 'PDF'),
  };

  const handle = async (format) => {
    setRunning(true);
    try {
      const res = await onExport(format);
      // A second click while the first is still running is not a failure and
      // has nothing to say.
      if (!res || res.reason === 'export-busy') return;
      if (res.ok) {
        toast.success(`${res.rows ?? 0} ${tval('export-rows-exported', 'rows exported')}`);
        return;
      }
      const [key, fallback] = _REASONS[res.reason] || _REASONS['export-failed'];
      const limit = res.limit ? ` (${res.limit})` : '';
      toast.error(`${tval(key, fallback)}${limit}`);
    } finally {
      setRunning(false);
    }
  };

  const working = busy || running;

  return (
    <Dropdown align={align}>
      <Dropdown.Toggle
        variant={variant}
        size={size}
        disabled={disabled || working}
        id="export-menu"
      >
        {working
          ? <Spinner animation="border" size="sm" className="me-1" role="status" />
          : <ExportIcon className="me-1" />}
        {working ? tval('exporting', 'Exporting…') : tval('export', 'Export')}
      </Dropdown.Toggle>
      <Dropdown.Menu>
        {formats.map((format) => (
          <Dropdown.Item key={format} onClick={() => handle(format)}>
            {labels[format] || format}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default ExportButton;
