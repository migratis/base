import Table from 'react-bootstrap/Table';

// Shared inline rendering for embed_in_parent children (sandbox merged tabs).
// A parent display passes the child descriptors ({entity, fk_field, fields})
// plus the fetched rows ({Child: [{id, data}]}); for the given parent record we
// show one compact sub-table per child entity, filtered to that parent via its
// FK. Used by every record-oriented display (table/cards/list/masonry) so the
// inline rendering stays identical regardless of the parent's display mode.

export const getEmbeddedSections = (record, embeddedChildren = [], embeddedRecords = {}) =>
  (embeddedChildren || [])
    .map((child) => ({
      child,
      rows: (embeddedRecords[child.entity] || []).filter(
        (row) => String((row.data || {})[child.fk_field]) === String(record.id)
      ),
    }))
    .filter((s) => s.rows.length > 0);

const EmbeddedChildren = ({ record, embeddedChildren = [], embeddedRecords = {}, t }) => {
  const tval = (key, fallback) => (t ? t(key, fallback) : fallback || key);
  const sections = getEmbeddedSections(record, embeddedChildren, embeddedRecords);
  if (sections.length === 0) return null;
  return (
    <div className="embedded-children">
      {sections.map(({ child, rows }) => (
        <div key={child.entity} className="mb-2">
          <div className="small fw-bold text-muted mb-1">
            {tval(child.entity, child.entity)} ({rows.length})
          </div>
          <Table size="sm" bordered className="mb-0 bg-white">
            <thead>
              <tr>
                {child.fields.map((f) => (
                  <th key={f.name} className="small">{tval(f.label, f.label)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  {child.fields.map((f) => {
                    const v = (row.data || {})[f.name];
                    return (
                      <td key={f.name} className="small">
                        {v === null || v === undefined || v === '' ? '—' : String(v)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ))}
    </div>
  );
};

export default EmbeddedChildren;
