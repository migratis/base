// -----------------------------------------------------------------------------
// The two numbers and the one separator the importer is built around, in a file
// with no imports of its own so that `coerce.js`, `index.js` and `runImport.js`
// can each have them without importing one another.
// -----------------------------------------------------------------------------

//: The list separator a multi-value cell is split on — `mapping.LIST_JOIN`'s,
//: so a value this platform wrote into a spreadsheet survives the round trip
//: back into it unchanged.
export const LIST_JOIN = ', ';

//: A hard ceiling on one import, `EXPORT_MAX_ROWS`' sibling and for its reason
//: inverted: a file that imports its first 5 000 rows of 40 000 looks like it
//: worked. Past this the file is REFUSED, out loud, rather than truncated.
export const IMPORT_MAX_ROWS = 5000;

//: How many rows the type inference is shown. It is a sample, not the file:
//: the proposal travels to the backend as JSON and is read in a browser, and
//: two hundred rows is already more evidence than a column needs.
export const INFERENCE_SAMPLE_ROWS = 200;

//: What the file picker accepts. `.tsv` is a CSV whose sniffed delimiter is a
//: tab; `.xls` is NOT here — the old binary format is not a zip of XML and
//: this reader would answer nothing for it.
export const IMPORT_ACCEPT = '.csv,.tsv,.txt,.xlsx';
