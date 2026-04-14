import { useTranslation } from 'react-i18next';
import { UserForm } from './UserForm';

const Register = (props) => {
  const { t } = useTranslation('register');
  const profile = {
    first_name: "",
    last_name: "",
    birthdate: new Date(),
    address: "",
    zipcode: "",
    city: "",      
    country: null,   
    professional: false,                               
    company: "",
    taxnumber: ""				  
  }

  return (
    <>
      <header className="sticky-top">
        <div className="row">
          <div className="col-sm-12">
            <h2>{ t('register') }</h2>
          </div>
        </div>
      </header>
      <UserForm profile={profile} register={true}/>
    </>
  );

};

export default Register;
