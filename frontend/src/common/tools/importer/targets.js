// -----------------------------------------------------------------------------
// importTargets — which fields a file column may be mapped to.
//
// `../export/columns.js`, pointed the other way, and written here for its
// reason: the sandbox and every generated application have to offer the same
// list or a file that imports in the preview does not import in the shipped
// application. One function, both hosts.
//
// Two decisions it inherits from the export side, and one it does not.
//
// **A field the config hides is not offered.** `visible: false` is the owner
// saying that column is not part of the record's presentation, so the FORM has
// no control for it either — and this whole feature is "what the form could
// write, from a file". Honouring it here is what keeps those two the same set.
//
// **A field the viewer may not read never arrives**, so it can never become a
// target: the schema this reads was served under the viewer's own role.
//
// And the one that is not the export's: **a relation is offered only when its
// options were supplied.** A cell holds a parent's NAME and a create request
// takes its id, so without the target's `{value, label}` list there is nothing
// to resolve through — and an empty dropdown is the affordance without the
// thing it needs, which is the mistake `direct_create → form` exists to repair
// one layer up.
// -----------------------------------------------------------------------------

/**
 * @param {object} entity    `{name, fields: [], relationships: []}`
 * @param {object} config    the entity's sandbox/entity config
 * @param {object} opts      `{relationOptions: {field_name: [{value,label}]}}`
 * @returns {Array} `[{name, description, field_type, choices, required, options}]`
 */
export function importTargets(entity, config = {}, opts = {}) {
  const { relationOptions = {} } = opts;
  const fieldsConfig = config?.fields || {};
  const relsConfig = config?.relationships || {};

  const fields = (entity?.fields || [])
    .filter((f) => fieldsConfig[f.name]?.visible !== false)
    .map((f) => ({
      name: f.name,
      description: fieldsConfig[f.name]?.label || f.description || f.name,
      field_type: f.field_type,
      // The domain is the FIELD's — `stamp_enum_field_options`' rule, applied
      // where the value is read rather than where it is displayed.
      //
      // The fallback is not optional. Only ONE of the two hosts hands the
      // browser a field's own `choices`: codegen bakes them into `ENTITY`, and
      // the sandbox schema carries none at all — there an enum's domain
      // arrives as the config's stamped `options`, which is the same list with
      // the label in the language it was written in. Without this, a file
      // holding the LABEL imports in the generated application and is refused
      // with `invalid-choice` in the preview.
      choices: (f.choices && f.choices.length)
        ? f.choices
        : (fieldsConfig[f.name]?.options || []),
      required: fieldsConfig[f.name]?.required ?? f.required ?? false,
    }));

  const relations = (entity?.relationships || [])
    .filter((r) => r.field_name && relsConfig[r.field_name]?.visible !== false)
    .map((r) => ({
      name: r.field_name,
      description: relsConfig[r.field_name]?.label || r.related_entity || r.field_name,
      field_type: r.relation_type === 'many_to_many' ? 'm2m' : 'fk',
      choices: [],
      required: !!relsConfig[r.field_name]?.required,
      options: relationOptions[r.field_name] || [],
    }));

  return [...fields, ...relations];
}

export default importTargets;
