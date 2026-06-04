import SelectField from './SelectField';
import { COUNTRIES } from './countries';

// Drop-in SelectField that ships with the ISO 3166-1 country list so the AI
// sandbox-config interpreter does not need to enumerate options for every
// country-typed field. If a caller passes its own `options` (e.g. an
// explicit shipping-zone subset), those win.
export default function CountryField({ options, isSearchable = true, ...props }) {
  const opts = options && options.length ? options : COUNTRIES;
  return <SelectField {...props} options={opts} isSearchable={isSearchable} />;
}
