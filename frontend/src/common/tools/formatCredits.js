// Credits are fractionable — an operation served by a cheap model costs a
// fraction of what it costs on an expensive one — so every place that shows a
// credit figure has to agree on how to render one.
//
// Two decimals is the unit the backend actually debits in (see
// credits.models.quantize_credits), so nothing is ever displayed at a precision
// the system cannot charge. Trailing zeros are trimmed: a balance reads "10",
// not "10.00", while a real fraction keeps its places — "0.85".
//
// Lives in common/ rather than in the credits module because the generator's
// confirm-spend modal needs it too, and the generator must keep working when
// the optional credits module is not installed.
export const formatCredits = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) return '0';
  // Round first: toFixed alone would render 0.005 as "0.01" in some engines and
  // "0.00" in others, and a price that disagrees with the debit is a bug report.
  const rounded = Math.round(number * 100) / 100;
  return String(rounded);
};

export default formatCredits;
