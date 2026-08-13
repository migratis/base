// -----------------------------------------------------------------------------
// pdf — the table as a document.
//
// **pdfmake, not jsPDF.** jsPDF's built-in fonts are the standard 14, which are
// WinAnsi: Romanian `ș`/`ț` (`Șterge` is in the generated apps' own vocabulary)
// and a fair amount of Central European text come out as garbage unless a TTF
// is embedded by hand. A PDF that cannot spell the application's own language
// is the same class of bug as a prompt rule whose trigger words were English.
// pdfmake embeds a Latin font and gets this right without being asked.
//
// **It is loaded on demand and its absence is honest.** The library is a real
// download, and most sessions never export a PDF, so it is behind a dynamic
// import; and a deployment whose `npm install` has not run yet gets a named
// refusal (`export-pdf-unavailable`) rather than a stack trace and a click that
// does nothing. Excel and CSV need nothing and keep working — the same posture
// as the smoke render degrading to a no-op without py-mini-racer, and the route
// editor hiding waypoint mode with no engine.
//
// **The document says what it is.** A PDF is the artefact that gets emailed, and
// a filtered export that does not say it is filtered is a false record — so the
// header carries the application, the table, the moment, and every filter and
// search term that was active when the button was pressed (D8).
// -----------------------------------------------------------------------------

export const PDF_MIME = 'application/pdf';

// Returned instead of a Blob when the library is not installed. A sentinel
// rather than a throw, because the caller distinguishes "not available" from
// "failed" and says two different things.
export const PDF_UNAVAILABLE = Symbol('pdf-unavailable');

// Past this many columns the page is turned on its side. Portrait A4 fits about
// this many readable columns; beyond it the text wraps to one word per line.
const LANDSCAPE_FROM_COLUMNS = 6;

const _tval = (t, key, fallback) => (t ? t(key, fallback) : fallback);

async function _loadPdfMake() {
  try {
    const [{ default: pdfMake }, { default: pdfFonts }] = await Promise.all([
      import('pdfmake/build/pdfmake'),
      import('pdfmake/build/vfs_fonts'),
    ]);
    // pdfmake has moved this around between majors; accept either shape rather
    // than pinning to one and breaking on an upgrade.
    const vfs = pdfFonts?.pdfMake?.vfs || pdfFonts?.vfs || pdfFonts;
    if (vfs) pdfMake.vfs = vfs;
    return pdfMake;
  } catch (err) {
    console.warn('[export] pdfmake is not installed', err);  // eslint-disable-line no-console
    return null;
  }
}

/** The header lines: what this document is, and what it is NOT (D8). */
export function describeExport(meta = {}, t) {
  const lines = [];
  if (meta.app) lines.push(meta.app);

  const when = meta.exportedAt ? new Date(meta.exportedAt) : new Date();
  lines.push(`${_tval(t, 'export-generated-on', 'Exported on')} ${when.toLocaleString()}`);

  const active = Object.entries(meta.filters || {})
    // The list's filter keys are prefixed by kind (fe_/fc_/ff_/ft_); the reader
    // wants the field, not the machinery.
    .filter(([, v]) => v !== '' && v !== null && v !== undefined)
    .map(([k, v]) => `${k.replace(/^(fe|fc|ff|ft)_/, '')}: ${v}`);
  if (meta.search) {
    active.unshift(`${_tval(t, 'export-search', 'Search')}: ${meta.search}`);
  }
  if (active.length) {
    lines.push(`${_tval(t, 'export-filtered', 'Filtered')} — ${active.join(' · ')}`);
  }
  return lines;
}

/**
 * @returns {Promise<Blob|typeof PDF_UNAVAILABLE>}
 */
export async function buildPdf({ title = '', headers = [], rows = [], meta = {}, t }) {
  const pdfMake = await _loadPdfMake();
  if (!pdfMake) return PDF_UNAVAILABLE;

  const landscape = headers.length > LANDSCAPE_FROM_COLUMNS;
  const subtitles = describeExport(meta, t);

  const body = [
    headers.map((h) => ({ text: String(h ?? ''), style: 'th' })),
    ...rows.map((row) => row.map((cell) => ({
      // The PDF carries the READING, not the typed value: it is a document, so
      // what belongs in it is what the user saw on screen.
      text: String(cell?.text ?? ''),
      alignment: cell?.type === 'number' ? 'right' : 'left',
    }))),
  ];

  const definition = {
    pageSize: 'A4',
    pageOrientation: landscape ? 'landscape' : 'portrait',
    pageMargins: [24, 32, 24, 36],
    defaultStyle: { fontSize: 8 },
    content: [
      title ? { text: title, style: 'title' } : null,
      subtitles.length ? { text: subtitles.join('\n'), style: 'subtitle' } : null,
      {
        table: { headerRows: 1, widths: headers.map(() => '*'), body },
        layout: 'lightHorizontalLines',
      },
    ].filter(Boolean),
    footer: (page, total) => ({
      text: `${_tval(t, 'export-page', 'Page')} ${page} / ${total}`,
      alignment: 'center',
      fontSize: 7,
      margin: [0, 12, 0, 0],
    }),
    styles: {
      title:    { fontSize: 14, bold: true, margin: [0, 0, 0, 4] },
      subtitle: { fontSize: 8, color: '#666666', margin: [0, 0, 0, 10] },
      th:       { bold: true, fontSize: 8 },
    },
  };

  return new Promise((resolve, reject) => {
    try {
      pdfMake.createPdf(definition).getBlob(resolve);
    } catch (err) {
      reject(err);
    }
  });
}

export default buildPdf;
