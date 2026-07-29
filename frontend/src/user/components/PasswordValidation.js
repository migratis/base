import { useEffect } from "react";
import { usePasswordValidation } from "../tools/usePasswordValidation";
import { 
	IoCheckmark as Checkmark,
	IoClose as Close 
} from 'react-icons/io5';
import { useTranslation } from 'react-i18next';

export const PasswordValidation = (props) => {
  const { t } = useTranslation('password');
	const [
		validLength,
		hasNumber,
		upperCase,
		lowerCase,
		match,
		specialChar,
	] = usePasswordValidation({
		firstPassword: props.password,
		secondPassword: props.confPassword,
		requiredLength: 10,
	});

  useEffect(() => {
    if (validLength && hasNumber && upperCase && lowerCase && match && specialChar) {
      props.setPasswordOk(true);
    } else {
      props.setPasswordOk(false);
    }
  }, [
    validLength, 
    hasNumber, 
    upperCase, 
    lowerCase,
    match, 
    specialChar,
    props
  ]);
  
  // Icon first, then the rule: the eye scans one column of state markers rather
  // than hunting for a marker at the ragged right edge of six different pills.
  // A rule that is not met yet is neutral, not red — nothing is wrong about an
  // empty password field, it is simply not done.
  const Rule = ({ met, children }) => (
    <li className={`password-rule${met ? ' password-rule--met' : ''}`}>
      <span className="password-rule-marker" aria-hidden="true">
        { met ? <Checkmark /> : <Close /> }
      </span>
      { children }
    </li>
  );

  return (
    <ul className="password-rules migratis-field">
      <Rule met={validLength}>{ t("password-length") }</Rule>
      <Rule met={hasNumber}>{ t("password-number") }</Rule>
      <Rule met={upperCase}>{ t("password-uppercase") }</Rule>
      <Rule met={lowerCase}>{ t("password-lowercase") }</Rule>
      <Rule met={specialChar}>{ t("password-special-characters") }</Rule>
      <Rule met={match}>{ t("password-match") }</Rule>
    </ul>
	);
}