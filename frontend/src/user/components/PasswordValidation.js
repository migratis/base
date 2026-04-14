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
  
  return (  
    <ul className="list-group migratis-field">
        <li className="list-group-item">
          { t("password-length") } 
          <span className="link">
            { validLength ? <Checkmark color={'#4e9a06'} title={"ok"} /> : <Close color={'#cc0000'} title={"ko"} /> }
          </span>
        </li>
        <li className="list-group-item">
          { t("password-number") }
          <span className="link">
            { hasNumber ? <Checkmark color={'#4e9a06'} title={"ok"} /> : <Close color={'#cc0000'} title={"ko"} /> }
          </span>
        </li>
        <li className="list-group-item">
          { t("password-uppercase") }
          <span className="link">
            { upperCase ? <Checkmark color={'#4e9a06'} title={"ok"} /> : <Close color={'#cc0000'} title={"ko"} /> }
          </span>
        </li>
        <li className="list-group-item">
          { t("password-lowercase") }
          <span className="link">
            { lowerCase ? <Checkmark color={'#4e9a06'} title={"ok"} /> : <Close color={'#cc0000'} title={"ko"} /> }
          </span>
        </li>
        <li className="list-group-item">
          { t("password-special-characters") }
          <span className="link">
           { specialChar ? <Checkmark color={'#4e9a06'} title={"ok"} /> : <Close color={'#cc0000'} title={"ko"} /> }
          </span>
        </li>
        <li className="list-group-item">
          { t("password-match") }
          <span className="link">
           { match ? <Checkmark color={'#4e9a06'} title={"ok"} /> : <Close color={'#cc0000'} title={"ko"} /> }
          </span>
        </li>
    </ul>
	);
}