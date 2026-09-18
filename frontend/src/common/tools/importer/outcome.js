// -----------------------------------------------------------------------------
// acceptedOrThrow — did that write actually happen?
//
// `common/tools/axios` **resolves on an error response** (`if (err.response)
// return err.response`), which is a deliberate choice the whole app is built
// on — and it means a `.then()` runs on a 422 exactly as it runs on a 200. A
// caller that does not look therefore reports success over a refusal, closes
// its modal, and leaves the user looking at a list where nothing was created.
//
// That is not a hypothetical: it is `saveOutcome.js`'s opening paragraph, it is
// `aiOutcome.js`'s, and it is what this module's first version got wrong on the
// very first duplicate name somebody imported.
//
// **The status is read before the body**, which is the rule
// `generator/services/aiTransport.js` states for the AI transport. Only where
// there is no status to read — a caller that already unwrapped to `.data` —
// does the envelope decide, and then by the documented contract and nothing
// looser: *a successful body's `detail` is an ARRAY of i18n keys*, so a
// `detail` that is anything else is a failure, named or not.
// -----------------------------------------------------------------------------

/** The thrown shape, so `describeFailure` reads it the way it reads an axios
 *  rejection: `error.response.data.detail` or `error.detail`. */
export class WriteRefused extends Error {
  constructor(body, status) {
    super('write-refused');
    this.name = 'WriteRefused';
    this.detail = body && typeof body === 'object' ? body.detail : body;
    this.status = status;
    this.response = { status, data: body };
  }
}

/**
 * Return what a write answered, or throw `WriteRefused`.
 *
 * Takes either an axios response (the status decides) or an already-unwrapped
 * body (the `detail` envelope decides). Anything else — a host whose create
 * returns its own value — is passed through: this module refuses writes it can
 * prove were refused, and invents no other opinion.
 */
export function acceptedOrThrow(result) {
  if (result && typeof result.status === 'number') {
    if (result.status >= 200 && result.status < 300) return result.data ?? result;
    throw new WriteRefused(result.data, result.status);
  }
  if (result && typeof result === 'object' && 'detail' in result) {
    const { detail } = result;
    if (Array.isArray(detail) && detail.some((entry) => entry && entry.success)) {
      return result;
    }
    throw new WriteRefused(result);
  }
  return result;
}

export default acceptedOrThrow;
